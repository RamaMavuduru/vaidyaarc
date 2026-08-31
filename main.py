from app.workflow import build_vaidyaarc_graph


def create_fresh_case_state():
    return {
        "patient_id": "TEST001",
        "session_id": "SESSION001",
        "language": "English",
        "patient_profile": {
            "age": 30,
            "medical_conditions": [],
            "allergies": []
        },
        "previous_history": [],
        "conversation_history": [],
        "extracted_information": {},
        "chief_complaint": None,
        "nature_of_pain": None,
        "location": None,
        "duration": None,
        "severity": None,
        "associated_symptoms": [],
        "current_message": "",
        "conversation_message": None,
        "next_question": None,
        "missing_information": [],
        "information_complete": False,
        "questions_asked": [],
    }


# Build the LangGraph workflow
graph = build_vaidyaarc_graph()


# Initial patient state
state = create_fresh_case_state()


print("\n" + "=" * 60)

print("WELCOME TO VAIDYAARC")

print("AI-POWERED HEALTH INTAKE AND NAVIGATION SYSTEM")

print("=" * 60)

print("Type 'exit' to stop the conversation.")


while True:

    # Get patient input

    patient_message = input(
        "\nPatient: "
    )


    # Exit

    if patient_message.lower() == "exit":

        print(
            "\nVaidyaArc session ended."
        )

        break


    # Update current message

    state["current_message"] = patient_message

    # Run LangGraph

    result = graph.invoke(state)
    state.update(result)

    # Store patient message

    state["conversation_history"].append({

        "role": "patient",

        "message": patient_message

    })


    # Display AI response

    if state.get("conversation_message"):

        print(
            "\nVaidyaArc:",
            state["conversation_message"]
        )


        # Store AI message

        state["conversation_history"].append({

            "role": "assistant",

            "message":
                state["conversation_message"]

        })


    # Development state view

    print("\n" + "-" * 60)

    print("CURRENT INTERNAL STATE")

    print("-" * 60)


    print(
        "Chief Complaint:",
        state.get("chief_complaint")
    )

    print(
        "Nature of Pain:",
        state.get("nature_of_pain")
    )

    print(
        "Location:",
        state.get("location")
    )

    print(
        "Duration:",
        state.get("duration")
    )

    print(
        "Severity:",
        state.get("severity")
    )

    print(
        "Associated Symptoms:",
        state.get("associated_symptoms")
    )

    print(
        "Missing Information:",
        state.get("missing_information")
    )

    print(
        "Information Complete:",
        state.get("information_complete")
    )

    if state.get("information_complete"):
        print(
            "Red Flag Status:",
            state.get("red_flag_status")
        )
        print(
            "Red Flags:",
            state.get("red_flags")
        )
        print(
            "Red Flag Evidence:",
            state.get("red_flag_evidence")
        )
        print(
            "Immediate Attention Required:",
            state.get("immediate_attention_required")
        )
        print(
            "Red Flag Rule Hits:",
            state.get("red_flag_rule_hits")
        )