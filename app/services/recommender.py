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
    memorized_poem_ids = {h.poem_id for h in history if h.outcome == "memorized"}
    avg_score = sum(r.score for r in revisions) / len(revisions) if revisions else 0.0
    return {
        "recommendations_total": len(history),
        "memorized_total": len(memorized_poem_ids),
        "average_revision_score": round(avg_score, 2),
    }


def memorized_poems(session: Session, telegram_user_id: int) -> list[Poem]:
    memorized_events = [
        event
        for event in session.exec(
            select(RecommendationEvent).where(RecommendationEvent.telegram_user_id == telegram_user_id)
        ).all()
        if event.outcome == "memorized"
    ]
    memorized_events.sort(key=lambda event: event.created_at, reverse=True)

    result: list[Poem] = []
    seen: set[int] = set()
    for event in memorized_events:
        if event.poem_id in seen:
            continue
        poem = session.get(Poem, event.poem_id)
        if poem is None:
            continue
        seen.add(event.poem_id)
        result.append(poem)
    return result


def memorized_poem_brief_payloads(session: Session, telegram_user_id: int) -> list[dict]:
    memorized_events = [
        event
        for event in session.exec(
            select(RecommendationEvent).where(RecommendationEvent.telegram_user_id == telegram_user_id)
        ).all()
        if event.outcome == "memorized"
    ]
    memorized_events.sort(key=lambda event: event.created_at, reverse=True)

    payload: list[dict] = []
    seen: set[int] = set()
    for event in memorized_events:
        if event.poem_id in seen:
            continue
        poem = session.get(Poem, event.poem_id)
        if poem is None or poem.id is None:
            continue

        seen.add(event.poem_id)
        payload.append(
            {
                "id": int(poem.id),
                "title": poem.title,
                "author": poem.author,
                "memorized_at": event.created_at.strftime("%d.%m.%Y"),
            }
        )
    return payload


def filter_poems_by_preferences(poems: list[Poem], user: UserProfile) -> list[Poem]:
    filtered = poems
    if user.language_pref != "mixed":
        filtered = [poem for poem in filtered if poem.language == user.language_pref]
    if user.difficulty_pref != "medium":
        filtered = [poem for poem in filtered if poem.difficulty == user.difficulty_pref]
    if user.theme_pref != "mixed":
        filtered = [poem for poem in filtered if poem.theme == user.theme_pref]
    return filtered


def choose_poem(session: Session, user: UserProfile) -> Poem:
    history = session.exec(
        select(RecommendationEvent).where(RecommendationEvent.telegram_user_id == user.telegram_user_id)
    ).all()
    seen_counts = Counter([event.poem_id for event in history])
    memorized_poem_ids = {event.poem_id for event in history if event.outcome == "memorized"}
    last_poem_id = history[-1].poem_id if history else None

    poems = session.exec(select(Poem).where(Poem.is_active == True)).all()  # noqa: E712
    candidates = poems

    def score(poem: Poem) -> int:
        value = 0
        if user.language_pref in ("mixed", poem.language):
            value += 3
        if user.difficulty_pref == poem.difficulty:
            value += 2
        if user.theme_pref in ("mixed", poem.theme):
            value += 2

        if poem.id in memorized_poem_ids:
            value += 5

        value += min(2, seen_counts.get(poem.id, 0))

        # Avoid immediate same-poem repeats while still allowing periodic revision.
        if last_poem_id is not None and poem.id == last_poem_id:
            value -= 4

        return value

    candidates.sort(key=score, reverse=True)
    return candidates[0]


def select_memorized_poem_for_user(session: Session, telegram_user_id: int, poem_id: int) -> Poem | None:
    memorized_ids = {poem.id for poem in memorized_poems(session, telegram_user_id)}
    if poem_id not in memorized_ids:
        return None
    return session.get(Poem, poem_id)


def mark_poem_memorized(
    session: Session,
    telegram_user_id: int,
    poem_id: int,
    full_name: str,
    username: str,
    score: float = 1.0,
    note: str = "Memorized via bot memory check",
) -> None:
    upsert_user(session, telegram_user_id, full_name, username)

    poem = session.get(Poem, poem_id)
    if poem is None:
        return

    session.add(
        RevisionEvent(
            telegram_user_id=telegram_user_id,
            poem_id=poem_id,
            prompt_type="local_memory_check",
            score=score,
            notes=note,
        )
    )
    session.add(
        RecommendationEvent(
            telegram_user_id=telegram_user_id,
            poem_id=poem_id,
            outcome="memorized",
            score=score,
            feedback=note,
        )
    )
    session.commit()


def memorized_poems_reply(session: Session, telegram_user_id: int, ui_language: str = "en") -> str:
    ui_lang = normalize_ui_language(ui_language)
    poems = memorized_poems(session, telegram_user_id)
    if not poems:
        if ui_lang == "ru":
            return "Пока нет выученных стихов. Выучите хотя бы одно стихотворение, и оно появится в этом списке."
        return "No memorized poems yet. Learn at least one poem and it will appear in this list."

    lines: list[str] = []
    for idx, poem in enumerate(poems, start=1):
        if ui_lang == "ru":
            lines.append(f"{idx}. {poem.title} - {poem.author}")
        else:
            lines.append(f"{idx}. {poem.title} - {poem.author}")

    if not lines:
        if ui_lang == "ru":
            return "Список выученных стихов пока пуст."
        return "Memorized poems list is empty."

    if ui_lang == "ru":
        return (
            "Ниже представлены стихотворения и дата, когда Вы их выучили. "
            "При желании Вы можете проверить насколько хорошо помните произведение. "
            "Для этого нажмите на нужное стихотворение"
        )
    return (
        "Below are poems and the dates when you learned them. "
        "If you want, you can check how well you remember a poem. "
        "Tap the poem you want to revise."
    )


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
) -> tuple[str, int | None, str, dict | None]:
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
                None,
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
                None,
            )

    active_poems = session.exec(select(Poem).where(Poem.is_active == True)).all()  # noqa: E712
    matching_poems = filter_poems_by_preferences(active_poems, user)
    memorized_ids = {poem.id for poem in memorized_poems(session, telegram_user_id)}
    non_memorized_matching_poems = [poem for poem in matching_poems if poem.id not in memorized_ids]

    if not non_memorized_matching_poems:
        memorized_list = memorized_poems(session, telegram_user_id)
        if ui_lang == "ru":
            no_match_reply = "К сожалению, количество стихотворений ограничено, не могу подобрать подходящее Вам."
            if memorized_list:
                no_match_reply += "\n\nЖелаете повторить что-то из уже изученного?"
        else:
            no_match_reply = "Unfortunately, the poem collection is limited and I cannot find a suitable match for you."
            if memorized_list:
                no_match_reply += "\n\nWould you like to revise something you have already learned?"
        return no_match_reply, None, "no_matching_poems", None

    poem = non_memorized_matching_poems[0]
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
    poem_payload = {
        "id": poem.id,
        "title": poem.title,
        "author": poem.author,
        "language": poem.language,
        "difficulty": poem.difficulty,
        "theme": poem.theme,
        "text": poem.text,
    }
    return reply, poem.id, "recommendation", poem_payload
