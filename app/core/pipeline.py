from .prompt import SUMMARY_PROMPT
from .llm import call_llm_json
from .parse import coerce_json
from .models import MeetingResult, ActionItem

def summarize_and_extract(title: str, transcript: str) -> MeetingResult:
    print("DEBUG transcript being sent to LLM:", transcript[:500])
    prompt = SUMMARY_PROMPT + "\n\nTranscript:\n\n" + transcript
    raw = call_llm_json(prompt)
    data = coerce_json(raw)

    # Extract decisions + action items
    decisions = data.get("decisions") or []
    action_items_raw = data.get("action_items") or []
    action_items = []
    for ai in action_items_raw:
        if isinstance(ai, dict) and ai.get("task"):
            action_items.append(ActionItem(
                assignee=ai.get("assignee"),
                task=ai.get("task"),
                due_date=ai.get("due_date")
            ))

    # ✅ Fallback: if summary is empty, show transcript snippet instead
    summary_text = data.get("summary", "").strip()
    if not summary_text:
        summary_text = (
            "⚠️ Model did not generate a summary.\n\n"
            "Here is the extracted transcript instead:\n\n"
            + transcript[:500]
        )

    return MeetingResult(
        title=title,
        transcript=transcript,
        summary=summary_text,
        decisions=decisions,
        action_items=action_items,
        important_dates=data.get("important_dates") or [],
        other_notes=data.get("other_notes") or []
    )
