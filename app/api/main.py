from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv   # 🟢 ADD THIS

# 🟢 Load environment variables from .env
load_dotenv()

# Importing existing pipeline parts
from app.core.ingest import extract_text_from_upload, extract_texts_from_uploads
from app.core.pipeline import summarize_and_extract
from app.core.storage import save_meeting_result, list_meetings, get_meeting
from app.core.models import MeetingResult
from app.core.transcribe import transcribe_audio

app = FastAPI(title="Meeting Summarizer API")

# granting react frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_meeting(
    files: List[UploadFile] = File([]),
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    title: Optional[str] = Form("Untitled Meeting"),
):
    transcript = ""

    if files:
        if len(files) == 1:
            # 🟢 read bytes from FastAPI UploadFile asynchronously
            file_bytes = await files[0].read()
            transcript = extract_text_from_upload(
                type("Temp", (), {"filename": files[0].filename, "read": lambda self=None: file_bytes})()
            )
        else:
            texts = []
            for f in files:
                file_bytes = await f.read()
                temp_file = type("Temp", (), {"filename": f.filename, "read": lambda self=None, b=file_bytes: b})()
                texts.append(extract_text_from_upload(temp_file))
            transcript = "\n\n".join(texts)

    elif audio:
        file_ext = audio.filename.split(".")[-1]
        tmp_path = Path(f"/tmp/{uuid.uuid4()}.{file_ext}")
        with open(tmp_path, "wb") as f:
            f.write(await audio.read())
        transcript = transcribe_audio(str(tmp_path))

    elif text:
        transcript = text.strip()

    if not transcript:
        return {"error": "No transcript found."}, 400

    result: MeetingResult = summarize_and_extract(title=title, transcript=transcript)
    meeting_id = save_meeting_result(result)

    return {
        "id": meeting_id,
        "title": result.title,
        "transcript": result.transcript,
        "summary": result.summary,
        "decisions": result.decisions,
        "action_items": [ai.__dict__ for ai in result.action_items],
        "important_dates": result.important_dates,
        "other_notes": result.other_notes,
    }


@app.get("/api/meetings")
def get_all_meetings():
    return list_meetings()

@app.get("/api/meetings/{meeting_id}")
def get_single_meeting(meeting_id: str):
    return get_meeting(meeting_id)
