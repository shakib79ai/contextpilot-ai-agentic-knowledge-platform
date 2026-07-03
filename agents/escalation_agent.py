"""Human Escalation Agent: decides whether an answer can go straight to the
user, should be shown with a low-confidence flag, or must be withheld
pending human review. Does not touch the database directly — it only
annotates `state`; the API layer (backend/app/api/routes_query.py) persists
the resulting ReviewTask so agents stay independently unit-testable."""
from app.config import get_settings
from app.models.enums import AnswerStatus
from agents.state import AgentState


def run(state: AgentState) -> AgentState:
    settings = get_settings()
    confidence = state.get("confidence", 0.0)

    if confidence >= settings.confidence_auto_answer_threshold:
        state["status"] = AnswerStatus.auto_answered.value
        state["review_reason"] = None
    elif confidence < settings.confidence_escalation_threshold:
        state["status"] = AnswerStatus.escalated.value
        state["review_reason"] = (
            f"Confidence {confidence:.2f} below escalation threshold "
            f"{settings.confidence_escalation_threshold:.2f}; answer withheld pending review."
        )
    else:
        state["status"] = AnswerStatus.low_confidence.value
        state["review_reason"] = (
            f"Confidence {confidence:.2f} is between thresholds; answer shown but queued for audit."
        )

    return state
