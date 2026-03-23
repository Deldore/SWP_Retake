from pydantic import BaseModel


class PoemPayload(BaseModel):
    id: int
    title: str
    author: str
    language: str
    difficulty: str
    theme: str
    text: str


class PoemBriefPayload(BaseModel):
    id: int
    title: str
    author: str


class ChatRequest(BaseModel):
    telegram_user_id: int
    text: str
    full_name: str = ""
    username: str = ""
    ui_language: str = "en"


class AudioMessageRequest(BaseModel):
    telegram_user_id: int
    file_id: str
    duration_seconds: int = 0
    mime_type: str = "audio/ogg"
    full_name: str = ""
    username: str = ""
    ui_language: str = "en"


class MemorizedPoemRequest(BaseModel):
    telegram_user_id: int
    poem_id: int
    score: float = 1.0
    full_name: str = ""
    username: str = ""


class MemorizedPoemsRequest(BaseModel):
    telegram_user_id: int
    ui_language: str = "en"


class MemorizedPoemByIdRequest(BaseModel):
    telegram_user_id: int
    poem_id: int
    ui_language: str = "en"


class BotReply(BaseModel):
    reply_text: str
    recommended_poem_id: int | None = None
    action: str
    poem: PoemPayload | None = None
    memorized_poems: list[PoemBriefPayload] = []
