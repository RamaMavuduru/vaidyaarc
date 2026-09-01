# PHASE 1B DEBUGGING - ROOT CAUSE ANALYSIS

## ISSUE 1: DURATION EXTRACTION FAILURE

### Problem Description
Patient responses like "today morning", "1 day ago", "this morning", "since this morning" are returning duration=None even though the previous question was "When did this problem start?"

### Current Behavior
```
Previous Question: "When did this problem start?"
Patient Message: "today morning"
LLM Extraction Result: duration=None

Previous Question: "When did the fever start?"
Patient Message: "1 day ago"
LLM Extraction Result: duration=None
```

### Root Cause
The `intake_brain()` function (lines 130-195 in app/nodes.py) uses a hardcoded prompt that:

1. **Conservative Extraction Rule**: "Extract ONLY new information explicitly stated in the CURRENT PATIENT MESSAGE"
2. **Explicit Examples**: Prompt provides examples like:
   - "It started 2 days ago" → duration="2 days"
   But does NOT provide examples of natural language temporal expressions like:
   - "today morning" → ??? (no example given)
   - "1 day ago" → ??? (no example given)
   - "this morning" → ??? (no example given)
   - "since yesterday" → ??? (no example given)

3. **Missing Context**: The prompt doesn't teach the LLM that informal temporal language IS valid duration extraction

### Why It Fails
The LLM is being overly conservative because:
- It lacks positive examples of informal temporal language
- It interprets "extract ONLY explicitly stated" very strictly
- Without examples showing "today morning" should map to a duration concept, it returns None

### Solution Required
Enhance the `intake_brain()` prompt in `app/nodes.py` to:
1. Add explicit examples of natural language time expressions
2. Make clear that these ARE valid duration extractions
3. Teach the LLM to normalize informal expressions to meaningful duration representations

---

## ISSUE 2: PREMATURE COMPLETION MESSAGE

### Problem Description
System produces "Thank you. I have collected the initial information..." while:
- `information_complete = False`
- `missing_information = ['duration']`
- This violates the intended control flow

### Current Flow Trace
```
Turn N: Patient says "1 day ago"
  → intake_brain: duration=None (due to Issue 1)
  → merge: duration remains None
  → validate: no changes
  → determine_missing_information: missing=['duration'], complete=False
  → route: "need_more_info"
  → select_next_question: returns next_question="How severe is the pain?"
  → ask_next_question: sends "How severe is the pain?" ✓ Correct

Turn N+1: Patient says "very severe"
  → intake_brain: severity="very high"
  → merge: severity="very high"
  → validate: no changes
  → determine_missing_information: missing=['duration'], complete=False
  → route: "need_more_info"
  → select_next_question: questions_asked=['duration','severity'], missing=['duration']
                         next_field NOT FOUND (duration already in questions_asked)
                         returns next_question=None
  → ask_next_question: PROBLEM HERE:
      if not question:
          question = "Thank you. I have collected..."  ← SENDS COMPLETION
```

### Root Cause
The `ask_next_question()` function (lines 720-735) has flawed logic:

```python
def ask_next_question(state: VaidyaArcState):
    if state.get("information_complete") or not state.get("missing_information"):
        return {
            "conversation_message": "Thank you. I have collected the initial information about your concern.",
            "next_question": None
        }

    question = state.get("next_question")
    if not question:  # ← PROBLEM: This triggers even when information_complete=False
        question = "Thank you. I have collected the initial information about your concern."

    return {
        "conversation_message": question,
        "next_question": question
    }
```

**The logic error:**
- Line 1 correctly handles the case when information_complete=True
- But line 2 has `if not question:` which ALSO sends completion message
- This triggers when select_next_question returns next_question=None (meaning no more questions to ask, but data still missing)
- So a patient who refuses to answer or has no answer triggers the completion message

### Intended Control Flow
```
if information_complete:
    send completion message
elif next_question exists:
    send the question
else:
    do NOT send completion message (we're stuck waiting for answer)
```

### Current (Broken) Control Flow
```
if information_complete:
    send completion message
else if missing_information is empty:
    send completion message
else:
    question = next_question
    if not question:
        send completion message  ← ✗ WRONG: completes even when incomplete
    else:
        send question
```

### Solution Required
Change `ask_next_question()` to:
```python
def ask_next_question(state: VaidyaArcState):
    # Only send completion if we're actually complete
    if state.get("information_complete"):
        return {
            "conversation_message": "Thank you. I have collected the initial information about your concern.",
            "next_question": None
        }
    
    # If we have a question, ask it
    question = state.get("next_question")
    if question:
        return {
            "conversation_message": question,
            "next_question": question
        }
    
    # If no question and not complete, we're stuck - don't send completion
    # Just return without conversation_message
    return {
        "next_question": None
    }
```

---

## ISSUE 3: RED FLAG ROUTING FOR SEVERE CHEST PAIN

### Problem Description
Patient says "severe chest pain" but system doesn't evaluate red flags until ALL required intake fields are complete. For emergency conditions, this delays safety evaluation.

### Current Routing
```
intake_brain
  → merge_intake_information
  → validate_patient_state
  → determine_missing_information
    → if information_complete: evaluate_red_flags ✓
    → if not complete: ask_next_question
      → END (no red flag evaluation yet)
```

### Issue
For "severe chest pain":
1. Extracts chief_complaint="severe chest pain"
2. Maps to "pain" template: needs [nature_of_pain, location, duration, severity]
3. User provides nature_of_pain and location but missing duration/severity
4. System asks questions one by one
5. Only evaluates red flags AFTER all fields collected
6. This could delay emergency response

### But...
The direct red flag tests pass:
- Direct test with severity="very severe" + duration set → correctly identifies as red flag

So the red flag *logic* works. The question is about *when* to invoke it.

### Investigation Points
1. Should red flags be evaluated as soon as we have critical information (e.g., "severe chest pain" + severity)?
2. Or should we wait for complete intake?
3. The user said: "Do NOT weaken or bypass safety rules" - but this isn't about the rules, it's about when we apply them

### Likely Solution
After fixing Issues 1 & 2, the system should naturally:
1. Reach red flag evaluation earlier if duration extraction works (fewer missing fields)
2. Or, add an early red flag trigger for critical complaints like "severe chest pain" + "severe" severity

But we need to test after fixing 1 & 2 first.

---

## TESTING STRATEGY

After fixes, test:

### Test 1: Duration Extraction
- "today morning" → should extract as valid duration
- "1 day ago" → should extract as valid duration
- "this morning" → should extract as valid duration
- "since yesterday" → should extract as valid duration
- "for two days" → should extract as valid duration
- "since this morning" → should extract as valid duration

### Test 2: Completion Logic
- When information_complete=True → send completion message
- When information_complete=False and missing_information non-empty → never send completion message (even if no more questions)
- When information_complete=False and all missing fields asked → stay in questioning state, don't force completion

### Test 3: Red Flag Flow
- "severe chest pain" + complete data → triggers red flags
- Mild fever → doesn't trigger red flags
- Phase 1 stomach pain flow preserved
- No duplicate questions

### Test 4: Regression
- Existing stomach pain flow unchanged
- Phase 2A red flag rules unchanged
- Adaptive intake for fever/cough/headache preserved
