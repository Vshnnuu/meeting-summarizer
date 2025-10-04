from .prompt import SUMMARY_PROMPT
from .llm import call_llm_json
from .parse import coerce_json
from .models import MeetingResult, ActionItem

# 🟢 Helper: break transcript into smaller pieces
def chunk_text(text: str, max_chars: int = 4000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def summarize_and_extract(title: str, transcript: str) -> MeetingResult:
    print("DEBUG transcript being sent to LLM (first 500 chars):", transcript[:500])

    # --- 1️⃣ Chunk long transcripts ---
    chunks = chunk_text(transcript)
    chunk_summaries = []

    for chunk in chunks:
        # Prompt only for short summary at this stage
        chunk_prompt = f"Summarize this transcript chunk in 2–3 sentences:\n\n{chunk}"
        raw = call_llm_json(chunk_prompt)
        data = coerce_json(raw)

        # Store either structured summary or raw fallback
        if isinstance(data, dict) and data.get("summary"):
            chunk_summaries.append(data["summary"])
        elif isinstance(data, str):
            chunk_summaries.append(data)
        else:
            chunk_summaries.append("⚠️ No summary for this chunk.")

    # --- 2️⃣ Merge chunk summaries ---
    merged_summary_text = " ".join(chunk_summaries)

    # --- 3️⃣ Second pass: ask LLM for structured JSON from merged summary ---
    final_prompt = SUMMARY_PROMPT + "\n\nTranscript Summary:\n\n" + merged_summary_text
    raw = call_llm_json(final_prompt)
    data = coerce_json(raw)

    # --- 4️⃣ Parse structured response ---
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

    summary_text = data.get("summary", "").strip()
    if not summary_text:
        summary_text = merged_summary_text[:500]

    return MeetingResult(
        title=title,
        transcript=transcript,
        summary=summary_text,
        decisions=decisions,
        action_items=action_items,
        important_dates=data.get("important_dates") or [],
        other_notes=data.get("other_notes") or []
    )