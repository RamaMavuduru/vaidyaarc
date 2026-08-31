from pydantic import BaseModel, Field
from typing import Optional


class RedFlagResult(BaseModel):
    red_flag_status: str = Field(
        default="no_obvious_red_flags",
        description="One of: red_flags_detected, no_obvious_red_flags, insufficient_information"
    )
    red_flags: list[str] = Field(
        default_factory=list,
        description="List of detected emergency warning signals."
    )
    red_flag_evidence: list[str] = Field(
        default_factory=list,
        description="Evidence from the collected patient information that triggered the red flag."
    )
    immediate_attention_required: bool = Field(
        default=False,
        description="Whether the situation indicates a need for immediate attention."
    )
    red_flag_rule_hits: list[dict[str, str | list[str]]] = Field(
        default_factory=list,
        description="Rule identifiers and associated evidence for each triggered red-flag rule."
    )


class IntakeResult(BaseModel):

    chief_complaint: Optional[str] = Field(
        default=None,
        description="Main health complaint explicitly mentioned in the current patient message. "
                    "Only include this when the patient clearly states it in the current message."
    )

    duration: Optional[str] = Field(
        default=None,
        description="Duration explicitly mentioned in the current patient message."
    )

    severity: Optional[str] = Field(
        default=None,
        description="Severity explicitly mentioned in the current patient message."
    )

    nature_of_pain: Optional[str] = Field(
        default=None,
        description="Character of pain such as burning, sharp, dull, or cramping, if explicitly mentioned."
    )

    location: Optional[str] = Field(
        default=None,
        description="Body location explicitly mentioned in the current patient message."
    )

    associated_symptoms: list[str] = Field(
        default_factory=list,
        description="Additional symptoms explicitly mentioned in the current patient message. Use only explicit symptom names."
    )