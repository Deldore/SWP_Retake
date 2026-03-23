from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.models.schemas import AudioMessageRequest, BotReply, ChatRequest
from app.services.recommender import build_reply, record_audio_submission

router = APIRouter()


def audio_reply_text(ui_language: str) -> str:
    if ui_language == "ru":
        return (
            "Голосовое сообщение получено и сохранено в истории обучения.\n\n"
            "В этой версии проекта нет автоматической расшифровки (без AI/нейросетей). "
            "Отправьте строки стихотворения текстом, и я проверю запоминание."
        )
    return (
        "I received your audio message and saved it to the learner history.\n\n"
        "This version does not use AI/neural transcription. "
        "Please send recalled lines as text, and I will check memorization."
    )


@router.post("/chat", response_model=BotReply)
def chat(payload: ChatRequest, session: Session = Depends(get_session)) -> BotReply:
    reply_text, recommended_poem_id, action = build_reply(
        session,
        telegram_user_id=payload.telegram_user_id,
        text=payload.text,
        full_name=payload.full_name,
        username=payload.username,
        ui_language=payload.ui_language,
    )
    return BotReply(reply_text=reply_text, recommended_poem_id=recommended_poem_id, action=action)


@router.post("/audio-message", response_model=BotReply)
def audio_message(payload: AudioMessageRequest, session: Session = Depends(get_session)) -> BotReply:
    record_audio_submission(
        session,
        telegram_user_id=payload.telegram_user_id,
        file_id=payload.file_id,
        duration_seconds=payload.duration_seconds,
        mime_type=payload.mime_type,
        full_name=payload.full_name,
        username=payload.username,
    )
    return BotReply(
        reply_text=audio_reply_text(payload.ui_language),
        recommended_poem_id=None,
        action="audio_received",
    )
