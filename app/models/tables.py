from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True, unique=True)
    full_name: str = ""
    username: str = ""
    language_pref: str = "mixed"  # ru|en|mixed
    difficulty_pref: str = "medium"  # easy|medium|hard
    theme_pref: str = "mixed"
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserPreference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True)
    key: str
    value: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Poem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    author: str
    language: str
    difficulty: str
    theme: str
    text: str
    first_line: str
    source_hint: str = "public domain / educational use"
    notes: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True)
    poem_id: int = Field(index=True)
    outcome: str = "recommended"  # recommended|accepted|rejected|memorized|partial|audio_received
    score: float = 0.0
    feedback: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RevisionEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True)
    poem_id: int = Field(index=True)
    prompt_type: str = "recall"
    score: float = 0.0
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AudioSubmission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: int = Field(index=True)
    file_id: str
    duration_seconds: int = 0
    mime_type: str = "audio/ogg"
    status: str = "received"  # received|reviewed
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
