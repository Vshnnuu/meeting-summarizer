import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
from dotenv import load_dotenv
import os
from app.core.ingest import extract_text_from_upload, extract_texts_from_uploads
from app.core.pipeline import summarize_and_extract
from app.core.storage import init_db, save_meeting_result, list_meetings, get_meeting
from app.core.models import MeetingResult

load_dotenv()

st.set_page_config(page_title="AI Meeting Summarizer", page_icon="📝", layout="wide")

st.title("📝 AI Meeting Summarizer & Action Tracker")

with st.sidebar:
    st.header("Meetings")
    if st.button("🔄 Refresh"):
        st.rerun()
    meetings = list_meetings()
    for m in meetings:
        if st.button(f"📄 {m['title']} ({m['created_at'][:10]})", key=f"m_{m['id']}"):
            st.session_state['selected_meeting_id'] = m['id']

tab1, tab2 = st.tabs(["➕ New Summary", "📚 History"])

with tab1:
    st.subheader("Upload transcript or paste text")
    uploaded_files = st.file_uploader("Upload transcript(s) or meeting documents", type=["txt", "pdf", "docx"], accept_multiple_files=True)
    text_input = st.text_area("...or paste transcript here", height=240, placeholder="Paste your meeting transcript...")
    title = st.text_input("Meeting title", value="Untitled Meeting")
    run_btn = st.button("🚀 Generate Summary & Actions")

    if run_btn:
        if uploaded_files is None and not text_input.strip():
            st.error("Please upload a file or paste transcript text.")
        else:
            if uploaded_files:
                if len(uploaded_files) == 1:
                    transcript = extract_text_from_upload(uploaded_files[0])
                else:
                    transcript = extract_texts_from_uploads(uploaded_files)
            else:
                transcript = text_input.strip()
            with st.spinner("Thinking..."):
                result: MeetingResult = summarize_and_extract(title=title or "Untitled Meeting", transcript=transcript)

            st.success("Done!")
            st.markdown("### 📝 Summary")
            st.write(result.summary)

            if result.decisions:
                st.markdown("### 🧩 Key Decisions")
                for d in result.decisions:
                    st.markdown(f"- {d}")

            st.markdown("### ✅ Action Items")
            if not result.action_items:
                st.info("No action items found.")
            else:
                for i, item in enumerate(result.action_items, start=1):
                    st.markdown(f"**{i}.** *Assignee:* {item.assignee or '—'}  \
"
                                f"*Task:* {item.task}  \
"
                                f"*Due:* {item.due_date or '—'}")

            # Save to DB
            saved_id = save_meeting_result(result)
            st.success(f"Saved meeting #{saved_id}. See it in History.")

with tab2:
    st.subheader("Your past meetings")
    meetings = list_meetings()
    if not meetings:
        st.info("No meetings yet. Create one in the first tab.")
    else:
        selected_id = st.session_state.get('selected_meeting_id')
        if selected_id:
            m = get_meeting(selected_id)
            st.markdown(f"""### {m['title']}  
*Created:* {m['created_at']}""")

            st.markdown("#### 📝 Summary")
            st.write(m['summary'])

            if m['decisions']:
                st.markdown("#### 🧩 Decisions")
                for d in m['decisions']:
                    st.markdown(f"- {d}")

            st.markdown("#### ✅ Action Items")
            if not m['action_items']:
                st.info("No action items stored.")
            else:
                for i, item in enumerate(m['action_items'], start=1):
                    st.markdown(f"""**{i}.** *Assignee:* {item.get('assignee') or '—'}  \
            *Task:* {item.get('task')}  \
            *Due:* {item.get('due_date') or '—'}""")

            # Important Dates
            if m.get('important_dates'):
                st.markdown("#### 📅 Important Dates")
                for d in m['important_dates']:
                    st.markdown(f"- {d}")

            # Other Notes
            if m.get('other_notes'):
                st.markdown("#### 📝 Other Notes")
                for note in m['other_notes']:
                    st.markdown(f"- {note}")

        else:
            # Show list of all meetings if none is selected
            for m in meetings:
                st.markdown(f"""**{m['title']}**  
*Created:* {m['created_at']}  

{m['summary'][:300]}...""")

