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

        print("\n" + "=" * 60)
        print("PHASE 2B: RISK CONVERGENCE")
        print("=" * 60)
        print("Risk Level:", state.get("risk_level"))
        print("Risk Score:", state.get("risk_score"))
        print("Risk Contributing Factors:", state.get("risk_contributing_factors"))
        print("Risk Reasoning:", state.get("risk_reasoning"))
        print("Recommended Next Action:", state.get("recommended_next_action"))

        print("\n" + "=" * 60)
        print("PHASE 3: CLINICAL CASE REPRESENTATION")
        print("=" * 60)
        print("Case Generation Status:", state.get("case_generation_status"))
        clinical_case = state.get("clinical_case") or {}
        clinical_case_output = state.get("clinical_case_output") or {}
        print("Care Pathway Status:", clinical_case.get("care_pathway_status"))
        data_quality = clinical_case.get("data_quality") or {}
        print("Completeness Percentage:", f"{data_quality.get('completeness_percentage', 0.0)}%")
        print("Case Summary:", clinical_case.get("case_summary"))
        print("Next Steps:", clinical_case.get("next_steps"))
        print("Case Ready for Review:", clinical_case_output.get("case_ready_for_review"))

        print("\n" + "=" * 60)
        print("PHASE 4: CARE NAVIGATION & FACILITY MATCHING")
        print("=" * 60)
        print("Care Navigation Status:", state.get("care_navigation_status"))
        print("Navigation Explanation:", state.get("navigation_explanation"))
        print("Navigation Data Source:", state.get("navigation_source"))
        matched_facilities = state.get("matched_facilities") or []
        print(f"Matched Facilities Count: {len(matched_facilities)}")
        for idx, match in enumerate(matched_facilities[:3], start=1):
            fac = match.get("facility", {})
            dist = match.get("distance_km")
            dist_str = f"{dist:.1f} km" if dist is not None else "N/A"
            print(f"  {idx}. {fac.get('facility_name')} ({fac.get('facility_type')})")
            print(f"     Match Score: {match.get('match_score')}/100 [{match.get('match_tier')}] | Distance: {dist_str}")
            print(f"     Emergency Services: {fac.get('emergency_services')} | Verification: {fac.get('verification_status')}")
            print(f"     Summary: {match.get('match_summary')}")

        if state.get("monitoring_status"):
            print("\n" + "=" * 60)
            print("PHASE 5: FOLLOW-UP & PATIENT MONITORING")
            print("=" * 60)
            print("Monitoring Status:", state.get("monitoring_status"))
            print("Patient Trajectory:", state.get("patient_trajectory"))
            print("Risk Trend:", state.get("risk_trend"))
            print("New Signals:", state.get("new_signals"))
            print("Resolved Signals:", state.get("resolved_signals"))
            print("Next Monitoring Action:", state.get("next_monitoring_action"))
            print("Monitoring Explanation:", state.get("monitoring_explanation"))