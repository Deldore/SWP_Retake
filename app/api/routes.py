from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.db import get_session
from app.models.schemas import (
    AudioMessageRequest,
    BotReply,
    ChatRequest,
    MemorizedPoemByIdRequest,
    MemorizedPoemRequest,
    MemorizedPoemsRequest,
)
from app.services.recommender import (
    build_reply,
    mark_poem_memorized,
    memorized_poems as list_memorized_poems,
    memorized_poems_reply,
    poem_brief_payloads,
    record_audio_submission,
    select_memorized_poem_for_user,
)

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
    reply_text, recommended_poem_id, action, poem_payload = build_reply(
        session,
        telegram_user_id=payload.telegram_user_id,
        text=payload.text,
        full_name=payload.full_name,
        username=payload.username,
        ui_language=payload.ui_language,
    )
    memorized_list_payload: list[dict] = []
    if action == "no_matching_poems":
        memorized_list_payload = poem_brief_payloads(list_memorized_poems(session, payload.telegram_user_id))

    return BotReply(
        reply_text=reply_text,
        recommended_poem_id=recommended_poem_id,
        action=action,
        poem=poem_payload,
        memorized_poems=memorized_list_payload,
    )


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


@router.post("/memorized", response_model=BotReply)
def memorized(payload: MemorizedPoemRequest, session: Session = Depends(get_session)) -> BotReply:
    mark_poem_memorized(
        session,
        telegram_user_id=payload.telegram_user_id,
        poem_id=payload.poem_id,
        score=payload.score,
        full_name=payload.full_name,
        username=payload.username,
    )
    return BotReply(
        reply_text="Memorized poem has been saved.",
        recommended_poem_id=payload.poem_id,
        action="memorized_recorded",
    )


@router.post("/memorized-poems", response_model=BotReply)
def memorized_poems_list(payload: MemorizedPoemsRequest, session: Session = Depends(get_session)) -> BotReply:
    return BotReply(
        reply_text=memorized_poems_reply(
            session,
            telegram_user_id=payload.telegram_user_id,
            ui_language=payload.ui_language,
        ),
        recommended_poem_id=None,
        action="memorized_poems_list",
        memorized_poems=poem_brief_payloads(list_memorized_poems(session, payload.telegram_user_id)),
    )


@router.post("/memorized-poem", response_model=BotReply)
def memorized_poem(payload: MemorizedPoemByIdRequest, session: Session = Depends(get_session)) -> BotReply:
    poem = select_memorized_poem_for_user(session, payload.telegram_user_id, payload.poem_id)
    if poem is None:
        if payload.ui_language == "ru":
            text = "Стихотворение не найдено среди выученных."
        else:
            text = "Poem was not found among memorized items."
        return BotReply(reply_text=text, recommended_poem_id=None, action="memorized_poem_not_found")

    poem_payload = {
        "id": int(poem.id),
        "title": poem.title,
        "author": poem.author,
        "language": poem.language,
        "difficulty": poem.difficulty,
        "theme": poem.theme,
        "text": poem.text,
    }
    return BotReply(
        reply_text="",
        recommended_poem_id=poem.id,
        action="memorized_poem_selected",
        poem=poem_payload,
    )
