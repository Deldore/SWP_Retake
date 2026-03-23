from pydantic import BaseModel


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


class BotReply(BaseModel):
    reply_text: str
    recommended_poem_id: int | None = None
    action: str
