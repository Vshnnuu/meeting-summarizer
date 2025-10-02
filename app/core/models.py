from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ActionItem(BaseModel):
    assignee: Optional[str] = None
    task: str
    due_date: Optional[str] = None  # e.g., '2025-10-03' or natural text

class MeetingResult(BaseModel):
    id: Optional[int] = None
    title: str = "Untitled Meeting"
    transcript: str
    summary: str
    decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    important_dates: List[str] = Field(default_factory=list)
    other_notes: List[str] = Field(default_factory=list)

