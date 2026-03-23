from __future__ import annotations

from collections import Counter
from datetime import datetime

from sqlmodel import Session, select

from app.models.tables import AudioSubmission, Poem, RecommendationEvent, RevisionEvent, UserPreference, UserProfile


def normalize_ui_language(ui_language: str) -> str:
    lowered = (ui_language or "en").strip().lower()
    return "ru" if lowered.startswith("ru") else "en"


def map_recall_note(note: str, ui_language: str) -> str:
    if ui_language != "ru":
        return note

    mapping = {
        "Strong recall": "Отличное воспроизведение",
        "Partial recall": "Частичное воспроизведение",
        "Weak recall": "Слабое воспроизведение",
        "No recall evidence.": "Недостаточно данных для оценки",
    }
    return mapping.get(note, note)


def format_recommendation_reply(poem: Poem, user: UserProfile, profile: dict, ui_language: str) -> str:
    if ui_language == "ru":
        return (
            "Подобрал стихотворение для вас.\n\n"
            "Стихотворение:\n"
            f"{poem.title} — {poem.author}\n"
            f"Язык: {poem.language.upper()} | Сложность: {poem.difficulty} | Тема: {poem.theme}\n\n"
            "Текст для изучения:\n"
            f"{poem.text}\n\n"
            "Что делать дальше:\n"
            "1. Прочитайте стихотворение 2-3 раза.\n"
            "2. Попробуйте вспомнить и отправьте 1-4 строки текстом.\n"
            "3. Используйте кнопку Memory check для проверки.\n\n"
            f"Почему выбрано: язык={user.language_pref}, сложность={user.difficulty_pref}, тема={user.theme_pref}.\n"
            f"Ваш прогресс: рекомендаций={profile['recommendations_total']}, выучено={profile['memorized_total']}, средний score={profile['average_revision_score']}."
        )

    return (
        "Your poem recommendation is ready.\n\n"
        "Poem:\n"
        f"{poem.title} — {poem.author}\n"
        f"Language: {poem.language.upper()} | Difficulty: {poem.difficulty} | Theme: {poem.theme}\n\n"
        "Text to learn:\n"
        f"{poem.text}\n\n"
        "What to do next:\n"
        "1. Read the poem 2-3 times.\n"
        "2. Try to recall and send 1-4 lines as text.\n"
        "3. Use the Memory check button to evaluate recall.\n\n"
        f"Why this choice: language={user.language_pref}, difficulty={user.difficulty_pref}, theme={user.theme_pref}.\n"
        f"Your progress: recommended={profile['recommendations_total']}, memorized={profile['memorized_total']}, avg score={profile['average_revision_score']}."
    )


def upsert_user(session: Session, telegram_user_id: int, full_name: str, username: str) -> UserProfile:
    user = session.exec(select(UserProfile).where(UserProfile.telegram_user_id == telegram_user_id)).first()
    if not user:
        user = UserProfile(telegram_user_id=telegram_user_id, full_name=full_name, username=username)
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        user.full_name = full_name or user.full_name
        user.username = username or user.username
        user.last_active_at = datetime.utcnow()
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def infer_preferences(message: str) -> dict[str, str]:
    text = message.lower()
    prefs: dict[str, str] = {}

    if any(word in text for word in ["рус", "russian", "пушкин", "лермонтов"]):
        prefs["language_pref"] = "ru"
    elif any(word in text for word in ["english", "англ", "frost", "shakespeare"]):
        prefs["language_pref"] = "en"

    if any(word in text for word in ["easy", "легк", "short", "корот"]):
        prefs["difficulty_pref"] = "easy"
    elif any(word in text for word in ["hard", "слож", "challenge", "сложно"]):
        prefs["difficulty_pref"] = "hard"

    theme_map = {
        "love": ["love", "любов", "роман"],
        "nature": ["nature", "природ", "snow", "лес", "зима"],
        "freedom": ["freedom", "свобод", "парус"],
        "life_choice": ["choice", "выбор", "life", "дорог"],
    }
    for theme, keywords in theme_map.items():
        if any(k in text for k in keywords):
            prefs["theme_pref"] = theme
            break
    return prefs


def persist_preferences(session: Session, user: UserProfile, prefs: dict[str, str]) -> UserProfile:
    for key, value in prefs.items():
        setattr(user, key, value)
        session.add(UserPreference(telegram_user_id=user.telegram_user_id, key=key, value=value))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def learner_profile_summary(session: Session, telegram_user_id: int) -> dict:
    history = session.exec(
        select(RecommendationEvent).where(RecommendationEvent.telegram_user_id == telegram_user_id)
    ).all()
    revisions = session.exec(
        select(RevisionEvent).where(RevisionEvent.telegram_user_id == telegram_user_id)
    ).all()
    completed = [h for h in history if h.outcome == "memorized"]
    avg_score = sum(r.score for r in revisions) / len(revisions) if revisions else 0.0
    return {
        "recommendations_total": len(history),
        "memorized_total": len(completed),
        "average_revision_score": round(avg_score, 2),
    }


def choose_poem(session: Session, user: UserProfile) -> Poem:
    seen_poem_ids = {
        event.poem_id
        for event in session.exec(
            select(RecommendationEvent).where(RecommendationEvent.telegram_user_id == user.telegram_user_id)
        ).all()
    }

    poems = session.exec(select(Poem).where(Poem.is_active == True)).all()  # noqa: E712
    candidates = [p for p in poems if p.id not in seen_poem_ids]
    if not candidates:
        candidates = poems

    def score(poem: Poem) -> int:
        value = 0
        if user.language_pref in ("mixed", poem.language):
            value += 3
        if user.difficulty_pref == poem.difficulty:
            value += 2
        if user.theme_pref in ("mixed", poem.theme):
            value += 2
        return value

    candidates.sort(key=score, reverse=True)
    return candidates[0]


def select_revision_candidate(session: Session, telegram_user_id: int) -> Poem | None:
    history = session.exec(
        select(RecommendationEvent).where(RecommendationEvent.telegram_user_id == telegram_user_id)
    ).all()
    if not history:
        return None
    counts = Counter([event.poem_id for event in history if event.outcome in {"accepted", "partial", "memorized"}])
    if not counts:
        return None
    weakest_poem_id = counts.most_common()[-1][0]
    return session.get(Poem, weakest_poem_id)


def check_memorization(poem: Poem, user_message: str) -> tuple[float, str]:
    poem_tokens = {token.strip(".,!?:;—-\n\t\"'“”«»").lower() for token in poem.text.split() if token.strip()}
    user_tokens = {token.strip(".,!?:;—-\n\t\"'“”«»").lower() for token in user_message.split() if token.strip()}
    if not user_tokens:
        return 0.0, "No recall evidence."
    overlap = len(poem_tokens & user_tokens) / max(1, len(poem_tokens))
    if overlap > 0.55:
        return overlap, "Strong recall"
    if overlap > 0.25:
        return overlap, "Partial recall"
    return overlap, "Weak recall"


def record_audio_submission(
    session: Session,
    telegram_user_id: int,
    file_id: str,
    duration_seconds: int,
    mime_type: str,
    full_name: str,
    username: str,
) -> None:
    upsert_user(session, telegram_user_id, full_name, username)
    session.add(
        AudioSubmission(
            telegram_user_id=telegram_user_id,
            file_id=file_id,
            duration_seconds=duration_seconds,
            mime_type=mime_type,
            status="received",
            notes="Accepted without automatic transcription",
        )
    )
    session.commit()


def build_reply(
    session: Session,
    telegram_user_id: int,
    text: str,
    full_name: str,
    username: str,
    ui_language: str = "en",
) -> tuple[str, int | None, str]:
    ui_lang = normalize_ui_language(ui_language)
    user = upsert_user(session, telegram_user_id, full_name, username)
    prefs = infer_preferences(text)
    if prefs:
        user = persist_preferences(session, user, prefs)

    lowered = text.lower()
    if any(k in lowered for k in ["repeat", "revision", "повтори", "провер", "recall"]):
        poem = select_revision_candidate(session, telegram_user_id)
        if poem:
            if ui_lang == "ru":
                reply = (
                    "Время повторения. Продолжите стихотворение:\n\n"
                    f"{poem.first_line}\n\n"
                    "Отправьте следующие строки текстом, и я оценю запоминание."
                )
            else:
                reply = (
                    "Time for revision. Continue this poem:\n\n"
                    f"{poem.first_line}\n\n"
                    "Send the next lines as text, and I will estimate recall."
                )
            return (
                reply,
                poem.id,
                "revision_prompt",
            )

    if any(k in lowered for k in ["memorized", "remember", "знаю", "выучил", "выучила", "помню", "continue"]):
        poem = select_revision_candidate(session, telegram_user_id)
        if poem:
            score, note = check_memorization(poem, text)
            localized_note = map_recall_note(note, ui_lang)
            session.add(
                RevisionEvent(
                    telegram_user_id=telegram_user_id,
                    poem_id=poem.id,
                    prompt_type="recall_check",
                    score=score,
                    notes=localized_note,
                )
            )
            outcome = "memorized" if score >= 0.55 else "partial" if score >= 0.25 else "recommended"
            session.add(
                RecommendationEvent(
                    telegram_user_id=telegram_user_id,
                    poem_id=poem.id,
                    outcome=outcome,
                    score=score,
                    feedback=localized_note,
                )
            )
            session.commit()
            if ui_lang == "ru":
                recall_reply = (
                    f"Результат проверки: {localized_note} (score={score:.2f}).\n\n"
                    "Продолжаем: можете запросить новую рекомендацию или отправить еще строки для проверки."
                )
            else:
                recall_reply = (
                    f"Recall result: {localized_note} (score={score:.2f}).\n\n"
                    "Next step: ask for a new recommendation or send more recalled lines for another check."
                )
            return (
                recall_reply,
                poem.id,
                "memorization_checked",
            )

    poem = choose_poem(session, user)
    session.add(
        RecommendationEvent(
            telegram_user_id=telegram_user_id,
            poem_id=poem.id,
            outcome="recommended",
            score=0.0,
            feedback="auto recommendation",
        )
    )
    session.commit()
    profile = learner_profile_summary(session, telegram_user_id)
    reply = format_recommendation_reply(poem, user, profile, ui_lang)
    return reply, poem.id, "recommendation"
