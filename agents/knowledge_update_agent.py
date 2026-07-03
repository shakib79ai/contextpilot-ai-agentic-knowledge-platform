"""Knowledge Update Agent: turns a reviewer's correction into a proposed
knowledge-base update when the correction looks like a factual change
rather than a stylistic tweak. Invoked from the review-resolution flow
(backend/app/api/routes_review.py) when a reviewer submits an `edit`
decision — not part of the main query-time agent graph."""
import difflib

from app.config import get_settings
from agents.llm_client import get_chat_client

STYLE_ONLY_SIMILARITY_THRESHOLD = 0.85


def _similarity_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _summarize_reason(original: str, corrected: str) -> str:
    settings = get_settings()
    chat_client = get_chat_client(settings)
    if chat_client is not None:
        try:
            return chat_client.complete(
                "You summarize factual corrections in one short sentence.",
                f"Original: {original}\n\nCorrected: {corrected}\n\n"
                "In one sentence, what factual change does the correction make?",
                temperature=0.0,
                max_tokens=120,
            ).strip()
        except Exception:  # noqa: BLE001
            pass
    return "Reviewer correction diverges materially from the original cited content."


def propose_update(original_content: str, corrected_content: str) -> dict | None:
    """Returns a proposal dict (`proposed_content`, `reason`) or `None` if
    the correction is judged to be style-only and not worth a KB update."""
    if not corrected_content or corrected_content.strip() == original_content.strip():
        return None

    similarity = _similarity_ratio(original_content, corrected_content)
    if similarity >= STYLE_ONLY_SIMILARITY_THRESHOLD:
        return None  # likely just phrasing/style — not a factual drift signal

    return {
        "proposed_content": corrected_content,
        "reason": _summarize_reason(original_content, corrected_content),
    }
