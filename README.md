# AI Meeting Summarizer & Action Tracker

A hackathon-friendly project that takes in meeting transcripts and produces:
- A concise summary
- Key decisions
- Structured action items (assignee (if mentioned), task, due_date (if available) and other_notes (if mentioned))

### Features
- Upload files **.txt, .pdf, .docx** or paste text directly 
- Supports OCR for scanned PDFs
- Supports audio transcription using **Faster-Whisper**
- Local data persistence for meeting history

## Tech
- **Meta LLaMA** (model family) served via **Cerebras** (fast inference)
- **Python 3.11 + Streamlit** UI
- **SQLite** for simple persistence
- **Docker** for portable deployment

## Quick Start (Local)
1) Create a virtualenv and install deps:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
brew install poppler tesseract ffmpeg   # for OCR + audio decoding
```
3) Run the app:
```bash
streamlit run app/main.py
```

> If Cerebras is not set up, the app will fall back to a lightweight mock so you can test the UI end-to-end.


## Environment
- `LLM_PROVIDER`: one of `cerebras`, `mock`
- `CEREBRAS_API_BASE`: base URL for Cerebras (e.g., `https://api.cerebras.ai/v1`) — adjust per docs
- `CEREBRAS_API_KEY`: your key/tokens

## Docker
Build & run:
```bash
docker build -t meeting-summarizer .
docker run -p 8501:8501 --env-file .env meeting-summarizer
```

## Notes
- The `cerebras` client is implemented assuming `/chat/completions` API schema. Adjust fields per your actual Cerebras endpoint docs if needed.
