import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from dotenv import load_dotenv

from app.core.ingest import extract_text_from_upload, extract_texts_from_uploads
from app.core.pipeline import summarize_and_extract
from app.core.storage import init_db, save_meeting_result, list_meetings, get_meeting
from app.core.models import MeetingResult

load_dotenv()
st.set_page_config(page_title="AI Meeting Summarizer", page_icon="📝", layout="wide")

# --- Helper: render action items nicely (only border, transparent background) ---
def render_action_items(items):
    if not items:
        st.info("No action items found.")
        return

    for i, item in enumerate(items, start=1):
        # handle dict (from DB) and object (from MeetingResult)
        if isinstance(item, dict):
            assignee = item.get("assignee") or "—"
            task = item.get("task") or "—"
            due = item.get("due_date") or "—"
        else:
            assignee = getattr(item, "assignee", None) or "—"
            task = getattr(item, "task", None) or "—"
            due = getattr(item, "due_date", None) or "—"

        st.markdown(
            f"""
            <div style="
                border: 1px solid #6c757d;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
                background-color: transparent;
            ">
                <b>{i}. Assignee:</b> {assignee}<br>
                <b>Task:</b> {task}<br>
                <b>Due Date:</b> {due}
            </div>
            """,
            unsafe_allow_html=True
        )

# --- Sidebar: History ---
with st.sidebar:
    st.header("📜 History")
    init_db()
    meetings = list_meetings()
    if not meetings:
        st.caption("No meetings saved yet.")
    else:
        for m in meetings:
            if st.button(f"{m['title']} • {m['created_at']}", key=f"m-{m['id']}"):
                st.session_state["selected_meeting_id"] = m["id"]

st.title("📝 AI Meeting Summarizer & Action Tracker")

# --- If a saved meeting is selected, show its details ---
sel_id = st.session_state.get("selected_meeting_id")
if sel_id:
    m = get_meeting(sel_id)
    if not m:
        st.warning("Could not load this meeting.")
    else:
        st.subheader(m["title"])
        st.markdown("### 📝 Summary")
        st.write(m["summary"] or "—")

        if m["decisions"]:
            st.markdown("### 🧩 Key Decisions")
            for d in m["decisions"]:
                st.markdown(f"- {d}")

        st.markdown("### ✅ Action Items")
        render_action_items(m.get("action_items") or [])

        if m.get("important_dates"):
            st.markdown("### 📅 Important Dates")
            for d in m["important_dates"]:
                st.markdown(f"- {d}")

        if m.get("other_notes"):
            st.markdown("### 📝 Other Notes")
            for n in m["other_notes"]:
                st.markdown(f"- {n}")

        st.divider()
        if st.button("← Back"):
            st.session_state.pop("selected_meeting_id", None)

# --- Otherwise, show upload/paste form ---
else:
    with st.form("input-form"):
        title = st.text_input("Meeting title", "Untitled Meeting")
        uploaded_files = st.file_uploader(
            "Upload transcript files (.txt, .pdf, OCR PDF, .docx, audio)",
            type=["txt", "pdf", "docx", "mp3", "wav", "m4a"],
            accept_multiple_files=True,
        )
        text_input = st.text_area("…or paste raw transcript text here", height=200)
        run_btn = st.form_submit_button("🚀 Generate Summary & Actions")

    if run_btn:
        if (not uploaded_files) and (not text_input.strip()):
            st.error("Please upload a file or paste transcript text.")
            st.stop()

        # --- Build transcript ---
        if uploaded_files:
            file_name = uploaded_files[0].name.lower()

            if file_name.endswith((".mp3", ".wav", ".m4a")):
                st.info("🎙️ Transcribing audio... please wait (first run may take ~30 s)")
                transcript = extract_text_from_upload(uploaded_files[0])
                st.success("✅ Audio transcription complete.")
            elif len(uploaded_files) == 1:
                transcript = extract_text_from_upload(uploaded_files[0])
            else:
                transcript = extract_texts_from_uploads(uploaded_files)
        else:
            transcript = text_input.strip()

        # --- Summarization ---
        with st.spinner("🧠 Summarizing..."):
            result: MeetingResult = summarize_and_extract(
                title=title or "Untitled Meeting",
                transcript=transcript,
            )

        # --- Persist & display ---
        save_meeting_result(result)
        st.success("Done! Saved to history.")

        st.markdown("### 📝 Summary")
        st.write(result.summary or "—")

        if result.decisions:
            st.markdown("### 🧩 Key Decisions")
            for d in result.decisions:
                st.markdown(f"- {d}")

        st.markdown("### ✅ Action Items")
        render_action_items(result.action_items)

        if result.important_dates:
            st.markdown("### 📅 Important Dates")
            for d in result.important_dates:
                st.markdown(f"- {d}")

        if result.other_notes:
            st.markdown("### 📝 Other Notes")
            for n in result.other_notes:
                st.markdown(f"- {n}")
