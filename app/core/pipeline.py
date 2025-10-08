from datetime import datetime
from .prompt import SUMMARY_PROMPT
from .llm import call_llm_json
from .parse import coerce_json
from .models import MeetingResult, ActionItem
import time



def summarize_and_extract(title: str, transcript: str) -> MeetingResult:
    """
    Single-step optimized summarization:
    - Sends the entire transcript to the LLM once (no chunk loop)
    - Uses structured JSON prompt (from prompt.py)
    - Returns a fully populated MeetingResult object
    - Fast: 10–15s typical latency
    """
    t_start = time.time()
    print("DEBUG transcript being sent to LLM (first 500 chars):", transcript[:500])
    print(f"📏 Transcript length: {len(transcript)} characters")

    # ✅ Build the complete structured prompt
    t_prompt = time.time()
    full_prompt = SUMMARY_PROMPT + transcript
    print(f"⚙️ Prompt built in {time.time() - t_prompt:.2f}s")

    # 🚀 Call LLM once
    t_llm = time.time()
    raw = call_llm_json(full_prompt)
    print(f"🧠 LLM call finished in {time.time() - t_llm:.2f}s")

    # Parse and extract
    t_parse = time.time()
    data = coerce_json(raw)
    print(f"🧩 JSON parsed in {time.time() - t_parse:.2f}s")

    # ✅ Extract structured fields safely
    summary = data.get("summary", "").strip()
    decisions = data.get("decisions") or []
    action_items_raw = data.get("action_items") or []
    important_dates = data.get("important_dates") or []
    other_notes = data.get("other_notes") or []

    # ✅ Normalize action items
    action_items = []
    for ai in action_items_raw:
        if isinstance(ai, dict) and ai.get("task"):
            action_items.append(
                ActionItem(
                    assignee=ai.get("assignee") or "Unassigned",
                    task=ai.get("task"),
                    due_date=ai.get("due_date") or "—",
                )
            )

    print(f"✅ Total summarize_and_extract() time: {time.time() - t_start:.2f}s")

    return MeetingResult(
        title=title,
        transcript=transcript,
        summary=summary,
        decisions=decisions,
        action_items=action_items,
        important_dates=important_dates,
        other_notes=other_notes,
    )
