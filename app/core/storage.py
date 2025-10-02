import os, json, sqlite3
from typing import List, Dict, Any
from .models import MeetingResult, ActionItem

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "meetings.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS meetings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                transcript TEXT,
                summary TEXT,
                decisions TEXT,        -- JSON list
                action_items TEXT,     -- JSON list
                important_dates TEXT,  -- JSON list
                other_notes TEXT,      -- JSON list
                created_at TEXT
            )"""
        )
        con.commit()

def save_meeting_result(result: MeetingResult) -> int:
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            """INSERT INTO meetings(
                   title, transcript, summary, decisions, action_items, important_dates, other_notes, created_at
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result.title,
                result.transcript,
                result.summary,
                json.dumps(result.decisions, ensure_ascii=False),
                json.dumps([ai.dict() for ai in result.action_items], ensure_ascii=False),
                json.dumps(result.important_dates, ensure_ascii=False),
                json.dumps(result.other_notes, ensure_ascii=False),
                result.created_at
            )
        )
        con.commit()
        return cur.lastrowid

def list_meetings() -> List[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        rows = cur.execute(
            "SELECT id, title, summary, created_at FROM meetings ORDER BY id DESC"
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r[0],
            "title": r[1],
            "summary": r[2],
            "created_at": r[3]
        })
    return out

def get_meeting(meeting_id: int) -> Dict[str, Any]:
    init_db()
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        row = cur.execute(
            """SELECT id, title, transcript, summary, decisions, action_items,
                      important_dates, other_notes, created_at
               FROM meetings WHERE id = ?""",
            (meeting_id,)
        ).fetchone()
    if not row:
        return {}
    return {
        "id": row[0],
        "title": row[1],
        "transcript": row[2],
        "summary": row[3],
        "decisions": json.loads(row[4]) if row[4] else [],
        "action_items": json.loads(row[5]) if row[5] else [],
        "important_dates": json.loads(row[6]) if row[6] else [],
        "other_notes": json.loads(row[7]) if row[7] else [],
        "created_at": row[8]
    }
