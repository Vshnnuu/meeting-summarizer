import os, json, sqlite3
from typing import List, Dict, Any
from .models import MeetingResult, ActionItem

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "meetings.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                transcript TEXT,
                summary TEXT,
                decisions TEXT,
                action_items TEXT,
                important_dates TEXT,
                other_notes TEXT,
                created_at TEXT
            )
            """
        )
        con.commit()

def save_meeting_result(m: MeetingResult) -> int:
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO meetings (
                title, transcript, summary, decisions, action_items,
                important_dates, other_notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                m.title,
                m.transcript,
                m.summary,
                json.dumps(m.decisions or []),
                json.dumps([ai.model_dump() for ai in m.action_items] if m.action_items else []),
                json.dumps(m.important_dates or []),
                json.dumps(m.other_notes or []),
                m.created_at,
            ),
        )
        con.commit()
        return cur.lastrowid

def list_meetings(limit: int = 50) -> List[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            """
            SELECT id, title, created_at, summary
            FROM meetings
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {"id": r[0], "title": r[1], "created_at": r[2], "summary": r[3] or ""}
        for r in rows
    ]

def get_meeting(meeting_id: int) -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute(
            """
            SELECT id, title, transcript, summary, decisions, action_items,
                   important_dates, other_notes, created_at
            FROM meetings
            WHERE id = ?
            """,
            (meeting_id,),
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
        "created_at": row[8],
    }

