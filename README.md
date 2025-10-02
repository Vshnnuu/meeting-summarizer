# AI Meeting Summarizer & Action Tracker

A hackathon-friendly project that takes in meeting transcripts and produces:
- A concise summary
- Key decisions
- Structured action items (assignee, task, due_date)

## Tech
- **Meta LLaMA** (model family) served via **Cerebras** (fast inference)
- **Python + Streamlit** UI
- **SQLite** for simple persistence
- **Docker** for portable deployment

## Quick Start (Local)
1) Create a virtualenv and install deps:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
2) Copy `.env.example` to `.env` and fill in values.
3) Run the app:
```bash
streamlit run app/app.py
```

> If you don't yet have Cerebras set up, the app will fall back to a lightweight mock so you can test the UI end-to-end.

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
- The `cerebras` client is implemented assuming an **OpenAI-compatible** `/chat/completions` API schema. Adjust fields per your actual Cerebras endpoint docs if needed.
- Audio upload (speech-to-text) can be added later as a stretch goal.
