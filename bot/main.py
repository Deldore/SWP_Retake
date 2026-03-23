import logging
import re
from html import escape
from itertools import zip_longest
from urllib.parse import urlparse, urlunparse

import requests
from requests import RequestException
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.error import BadRequest
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.core.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

TEXTS = {
    "en": {
        "start": "Hi! I am Poetry Bot.\nUse buttons below to get recommendations, run memory checks, and work with voice messages.",
        "help": (
            "/start - open interactive menu\n"
            "/help - show this help\n\n"
            "Recommended flow:\n"
            "1) Press 'Get recommendation'\n"
            "2) Choose language, difficulty, and theme\n"
            "3) Press 'Recommend now'\n"
            "4) Send remembered lines as text, or press 'Memory check'\n\n"
            "You can still type free text if you prefer."
        ),
        "menu_title": "Main menu. Choose an action:",
        "menu_recommend": "Get recommendation",
        "menu_memory": "Memory check",
        "menu_voice": "Voice message help",
        "menu_help": "Help",
        "menu_learned": "My memorized poems",
        "menu_lang": "Language: EN",
        "quick_new": "New recommendation",
        "quick_memory": "Memory check",
        "quick_main": "Main menu",
        "pref_prompt": "Choose preferences with buttons and press 'Recommend now'.",
        "not_selected": "not selected",
        "pref_language": "Language",
        "pref_difficulty": "Difficulty",
        "pref_theme": "Theme",
        "pref_ru": "Russian",
        "pref_en": "English",
        "pref_mixed": "Mixed",
        "pref_easy": "Easy",
        "pref_hard": "Hard",
        "pref_love": "Love",
        "pref_nature": "Nature",
        "pref_freedom": "Freedom",
        "pref_life": "Life choice",
        "recommend_now": "Recommend now",
        "reset": "Reset",
        "main_menu": "Main menu",
        "voice_help_text": "Send a voice message directly in chat.\nI will save it and ask you to send poem lines as text for memorization checking.",
        "mini_help_text": "Use 'Get recommendation' to build preferences through buttons.\nUse 'Memory check' when you want a revision prompt.\nYou can still send free text or voice at any time.",
        "required_alert": "Please select language, difficulty, and theme first.",
        "backend_unavailable": "Backend is temporarily unavailable. Please make sure API is running and try again.",
        "no_audio": "I received no audio.",
        "unexpected_error": "Unexpected error occurred. Please try again later.",
        "lang_switched": "Interface language switched to English.",
        "memory_request": "Memory check",
        "memory_prompt": "Try to write the poem from memory and send it in chat.",
        "memory_no_poem": "First get a recommendation, then start memory check.",
        "rec_new": "New recommendations",
        "rec_hide": "Hide text",
        "rec_show": "Show text",
        "mem_retry": "Try again",
        "mem_back": "Back",
        "mem_next": "Next poem",
        "mem_main": "Main menu",
        "mem_success": "Excellent! You reproduced the text without mistakes.\n\nReady for the next poem?",
    },
    "ru": {
        "start": "Привет! Я Poetry Bot.\nИспользуйте кнопки ниже: рекомендации, проверка памяти и работа с голосом.",
        "help": (
            "/start - открыть интерактивное меню\n"
            "/help - показать справку\n\n"
            "Рекомендуемый сценарий:\n"
            "1) Нажмите 'Подобрать стихотворение'\n"
            "2) Выберите язык, сложность и тему\n"
            "3) Нажмите 'Подобрать сейчас'\n"
            "4) Отправьте строки по памяти текстом или нажмите 'Проверка памяти'\n\n"
            "Можно также писать текст вручную."
        ),
        "menu_title": "Главное меню. Выберите действие:",
        "menu_recommend": "Подобрать стихотворение",
        "menu_memory": "Проверка памяти",
        "menu_voice": "Помощь по голосу",
        "menu_help": "Справка",
        "menu_learned": "Мои выученные стихи",
        "menu_lang": "Язык: RU",
        "quick_new": "Новая рекомендация",
        "quick_memory": "Проверка памяти",
        "quick_main": "Главное меню",
        "pref_prompt": "Выберите параметры кнопками и нажмите 'Подобрать сейчас'.",
        "not_selected": "не выбрано",
        "pref_language": "Язык",
        "pref_difficulty": "Сложность",
        "pref_theme": "Тема",
        "pref_ru": "Русский",
        "pref_en": "Английский",
        "pref_mixed": "Смешанный",
        "pref_easy": "Легко",
        "pref_hard": "Сложно",
        "pref_love": "Любовь",
        "pref_nature": "Природа",
        "pref_freedom": "Свобода",
        "pref_life": "Жизненный выбор",
        "recommend_now": "Подобрать сейчас",
        "reset": "Сброс",
        "main_menu": "Главное меню",
        "voice_help_text": "Отправьте голосовое сообщение прямо в чат.\nЯ сохраню его и попрошу прислать строки стихотворения текстом для проверки запоминания.",
        "mini_help_text": "Используйте 'Подобрать стихотворение' для выбора параметров кнопками.\nИспользуйте 'Проверка памяти', чтобы получить задание на повторение.\nМожно отправлять и текст, и голос в любой момент.",
        "required_alert": "Сначала выберите язык, сложность и тему.",
        "backend_unavailable": "Backend временно недоступен. Убедитесь, что API запущен, и попробуйте снова.",
        "no_audio": "Аудио не получено.",
        "unexpected_error": "Произошла ошибка. Попробуйте позже.",
        "lang_switched": "Язык интерфейса переключен на русский.",
        "memory_request": "Проверка памяти",
        "memory_prompt": "Попробуйте самостоятельно написать текст стихотворения по памяти и отправьте его в чат",
        "memory_no_poem": "Сначала получите рекомендацию, затем запускайте проверку памяти.",
        "rec_new": "Новые рекомендации",
        "rec_hide": "Скрыть текст",
        "rec_show": "Показать текст",
        "mem_retry": "Попробовать еще",
        "mem_back": "Назад",
        "mem_next": "К следующему стихотворению",
        "mem_main": "В главное меню",
        "mem_success": "Отлично! Вы воспроизвели текст без ошибок.\n\nГотовы перейти к следующему стихотворению?",
    },
}


def t(ui_lang: str, key: str) -> str:
    lang_block = TEXTS.get(ui_lang, TEXTS["en"])
    return lang_block.get(key, TEXTS["en"][key])


def get_ui_lang(context: ContextTypes.DEFAULT_TYPE, user=None) -> str:
    stored = context.user_data.get("ui_lang")
    if stored in {"ru", "en"}:
        return stored

    guessed = "en"
    if user is not None and getattr(user, "language_code", None):
        guessed = "ru" if str(user.language_code).lower().startswith("ru") else "en"

    context.user_data["ui_lang"] = guessed
    return guessed


def get_prefs(context: ContextTypes.DEFAULT_TYPE) -> dict[str, str]:
    prefs = context.user_data.get("prefs")
    if isinstance(prefs, dict):
        return prefs
    prefs = {}
    context.user_data["prefs"] = prefs
    return prefs


def get_active_poem(context: ContextTypes.DEFAULT_TYPE) -> dict | None:
    poem = context.user_data.get("active_poem")
    if isinstance(poem, dict):
        return poem
    return None


def set_memory_mode(context: ContextTypes.DEFAULT_TYPE, enabled: bool) -> None:
    context.user_data["awaiting_memory_input"] = enabled


def is_memory_mode(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get("awaiting_memory_input", False))


def set_show_poem_text(context: ContextTypes.DEFAULT_TYPE, show: bool) -> None:
    context.user_data["show_poem_text"] = show


def current_show_poem_text(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return bool(context.user_data.get("show_poem_text", True))


def store_recommendation_state(context: ContextTypes.DEFAULT_TYPE, poem: dict) -> None:
    context.user_data["active_poem"] = poem
    set_show_poem_text(context, True)
    set_memory_mode(context, False)


def main_menu_keyboard(ui_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t(ui_lang, "menu_recommend"), callback_data="menu:recommend")],
            [InlineKeyboardButton(t(ui_lang, "menu_memory"), callback_data="menu:memory")],
            [InlineKeyboardButton(t(ui_lang, "menu_learned"), callback_data="menu:learned")],
            [InlineKeyboardButton(t(ui_lang, "menu_voice"), callback_data="menu:voice")],
            [InlineKeyboardButton(t(ui_lang, "menu_help"), callback_data="menu:help")],
            [InlineKeyboardButton(t(ui_lang, "menu_lang"), callback_data="menu:toggle_lang")],
        ]
    )


def quick_actions_keyboard(ui_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t(ui_lang, "quick_new"), callback_data="rec:new")],
            [InlineKeyboardButton(t(ui_lang, "quick_memory"), callback_data="menu:memory")],
            [InlineKeyboardButton(t(ui_lang, "quick_main"), callback_data="menu:main")],
        ]
    )


def recommendation_actions_keyboard(ui_lang: str, show_text: bool) -> InlineKeyboardMarkup:
    hide_or_show = t(ui_lang, "rec_hide") if show_text else t(ui_lang, "rec_show")
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t(ui_lang, "rec_new"), callback_data="rec:new")],
            [
                InlineKeyboardButton(hide_or_show, callback_data="rec:toggle"),
                InlineKeyboardButton(t(ui_lang, "menu_memory"), callback_data="rec:memory"),
            ],
            [InlineKeyboardButton(t(ui_lang, "mem_main"), callback_data="menu:main")],
        ]
    )


def memorized_poems_keyboard(ui_lang: str, memorized_poems: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for poem in memorized_poems:
        poem_id = poem.get("id")
        title = str(poem.get("title", ""))
        if poem_id is None:
            continue
        rows.append([InlineKeyboardButton(title, callback_data=f"learned:open:{poem_id}")])

    rows.append([InlineKeyboardButton(t(ui_lang, "mem_main"), callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def memory_error_keyboard(ui_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(ui_lang, "mem_retry"), callback_data="mem:retry"), InlineKeyboardButton(t(ui_lang, "mem_back"), callback_data="mem:back")]]
    )


def memory_success_keyboard(ui_lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t(ui_lang, "mem_next"), callback_data="mem:next"), InlineKeyboardButton(t(ui_lang, "mem_main"), callback_data="menu:main")]]
    )


def recommendation_keyboard(prefs: dict[str, str], ui_lang: str) -> InlineKeyboardMarkup:
    language = prefs.get("language")
    difficulty = prefs.get("difficulty")
    theme = prefs.get("theme")

    def mark(current: str | None, value: str, label: str) -> str:
        return f"[x] {label}" if current == value else label

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(mark(language, "ru", t(ui_lang, "pref_ru")), callback_data="pref:lang:ru"),
                InlineKeyboardButton(mark(language, "en", t(ui_lang, "pref_en")), callback_data="pref:lang:en"),
                InlineKeyboardButton(mark(language, "mixed", t(ui_lang, "pref_mixed")), callback_data="pref:lang:mixed"),
            ],
            [
                InlineKeyboardButton(mark(difficulty, "easy", t(ui_lang, "pref_easy")), callback_data="pref:diff:easy"),
                InlineKeyboardButton(mark(difficulty, "hard", t(ui_lang, "pref_hard")), callback_data="pref:diff:hard"),
            ],
            [
                InlineKeyboardButton(mark(theme, "love", t(ui_lang, "pref_love")), callback_data="pref:theme:love"),
                InlineKeyboardButton(mark(theme, "nature", t(ui_lang, "pref_nature")), callback_data="pref:theme:nature"),
            ],
            [
                InlineKeyboardButton(mark(theme, "freedom", t(ui_lang, "pref_freedom")), callback_data="pref:theme:freedom"),
                InlineKeyboardButton(mark(theme, "life_choice", t(ui_lang, "pref_life")), callback_data="pref:theme:life_choice"),
            ],
            [
                InlineKeyboardButton(t(ui_lang, "recommend_now"), callback_data="pref:submit"),
                InlineKeyboardButton(t(ui_lang, "reset"), callback_data="pref:reset"),
            ],
            [InlineKeyboardButton(t(ui_lang, "main_menu"), callback_data="menu:main")],
        ]
    )


def recommendation_prompt_text(prefs: dict[str, str], ui_lang: str) -> str:
    language = prefs.get("language", t(ui_lang, "not_selected"))
    difficulty = prefs.get("difficulty", t(ui_lang, "not_selected"))
    theme = prefs.get("theme", t(ui_lang, "not_selected"))
    return (
        f"{t(ui_lang, 'pref_prompt')}\n\n"
        f"{t(ui_lang, 'pref_language')}: {language}\n"
        f"{t(ui_lang, 'pref_difficulty')}: {difficulty}\n"
        f"{t(ui_lang, 'pref_theme')}: {theme}"
    )


def build_preference_text(prefs: dict[str, str], ui_lang: str) -> str:
    if ui_lang == "ru":
        ru_language_map = {
            "ru": "русское",
            "en": "английское",
            "mixed": "смешанное",
        }
        ru_difficulty_map = {
            "easy": "легкое",
            "hard": "сложное",
        }
        ru_theme_map = {
            "love": "любовь",
            "nature": "природа",
            "freedom": "свобода",
            "life_choice": "жизненный выбор",
        }
        return (
            f"Хочу {ru_difficulty_map.get(prefs['difficulty'], 'легкое')} "
            f"{ru_language_map.get(prefs['language'], 'смешанное')} стихотворение на тему {ru_theme_map.get(prefs['theme'], 'природа')}"
        )

    language_map = {
        "ru": "Russian",
        "en": "English",
        "mixed": "mixed language",
    }
    difficulty_map = {
        "easy": "easy",
        "hard": "hard",
    }
    theme_map = {
        "love": "love",
        "nature": "nature",
        "freedom": "freedom",
        "life_choice": "life choices",
    }

    language = language_map.get(prefs["language"], "mixed language")
    difficulty = difficulty_map.get(prefs["difficulty"], "easy")
    theme = theme_map.get(prefs["theme"], "nature")
    return f"I want a {difficulty} {language} poem about {theme}"


def poem_language_label(poem_language: str, ui_lang: str) -> str:
    if ui_lang == "ru":
        return {"ru": "русский", "en": "английский"}.get(poem_language, poem_language)
    return {"ru": "Russian", "en": "English"}.get(poem_language, poem_language)


def poem_difficulty_label(poem_difficulty: str, ui_lang: str) -> str:
    if ui_lang == "ru":
        return {"easy": "легкая", "hard": "сложная", "medium": "средняя"}.get(poem_difficulty, poem_difficulty)
    return poem_difficulty


def poem_theme_label(poem_theme: str, ui_lang: str) -> str:
    if ui_lang == "ru":
        return {
            "love": "любовь",
            "nature": "природа",
            "freedom": "свобода",
            "life_choice": "жизненный выбор",
            "mixed": "смешанная",
        }.get(poem_theme, poem_theme)
    return poem_theme


def format_poem_lines(poem_text: str) -> str:
    lines = [line.strip() for line in poem_text.splitlines() if line.strip()]
    return "\n".join(f"   {escape(line)}" for line in lines)


def format_recommendation_message(poem: dict, ui_lang: str, show_text: bool) -> str:
    title = escape(str(poem.get("title", "")))
    author = escape(str(poem.get("author", "")))
    language = poem_language_label(str(poem.get("language", "")), ui_lang)
    difficulty = poem_difficulty_label(str(poem.get("difficulty", "")), ui_lang)
    theme = poem_theme_label(str(poem.get("theme", "")), ui_lang)

    if ui_lang == "ru":
        base = (
            "Подобрал стихотворение для вас.\n\n"
            "Стихотворение:\n"
            f"<b>{title} - {author}</b>\n"
            f"<i>Язык: {escape(language)}; Сложность: {escape(difficulty)}; Тематика: {escape(theme)}.</i>\n\n"
        )
        if show_text:
            base += f"<pre>{format_poem_lines(str(poem.get('text', '')))}</pre>\n\n"
        base += (
            "Прочитайте стихотворение, и если оно Вам понравилось:\n"
            "1. Прочитайте его еще 2-3 раза\n"
            "2. Попробуйте вспомнить и записать 1-4 строчки\n"
            "3. Для удобства проверки можете нажать на кнопку \"Скрыть текст\""
        )
        return base

    base = (
        "I picked a poem for you.\n\n"
        "Poem:\n"
        f"<b>{title} - {author}</b>\n"
        f"<i>Language: {escape(language)}; Difficulty: {escape(difficulty)}; Theme: {escape(theme)}.</i>\n\n"
    )
    if show_text:
        base += f"<pre>{format_poem_lines(str(poem.get('text', '')))}</pre>\n\n"
    base += (
        "Read the poem, and if you like it:\n"
        "1. Read it again 2-3 times\n"
        "2. Try to recall and write 1-4 lines\n"
        "3. You can press \"Hide text\" for easier memory check"
    )
    return base


def normalize_for_compare(text: str) -> list[str]:
    lowered = text.lower().replace("ё", "е")
    cleaned = re.sub(r"[^\w\s]", " ", lowered, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []
    return cleaned.split(" ")


def compare_poem_with_user(poem_text: str, user_text: str) -> tuple[int, str]:
    poem_words = normalize_for_compare(poem_text)
    user_words = normalize_for_compare(user_text)

    errors = 0
    marked_user_words: list[str] = []
    for poem_word, user_word in zip_longest(poem_words, user_words, fillvalue=None):
        if poem_word is None and user_word is not None:
            errors += 1
            marked_user_words.append(f"<u>{escape(user_word)}</u>")
            continue
        if poem_word is not None and user_word is None:
            errors += 1
            continue
        if poem_word != user_word:
            errors += 1
            marked_user_words.append(f"<u>{escape(str(user_word))}</u>")
        else:
            marked_user_words.append(escape(str(user_word)))

    return errors, " ".join(marked_user_words)


def backend_base_urls() -> list[str]:
    primary = settings.backend_public_url.rstrip("/")
    urls = [primary]

    parsed = urlparse(primary)
    if parsed.hostname == "backend":
        localhost_netloc = f"localhost:{parsed.port}" if parsed.port else "localhost"
        fallback = urlunparse(parsed._replace(netloc=localhost_netloc)).rstrip("/")
        if fallback not in urls:
            urls.append(fallback)

    return urls


def backend_post(path: str, payload: dict) -> dict:
    last_error: RequestException | None = None

    for base_url in backend_base_urls():
        try:
            response = requests.post(f"{base_url}{path}", json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except RequestException as exc:
            last_error = exc
            logger.warning("Backend request failed for %s%s: %s", base_url, path, exc)

    assert last_error is not None
    raise last_error


def backend_chat(payload: dict) -> dict:
    return backend_post("/api/chat", payload)


def backend_audio(payload: dict) -> dict:
    return backend_post("/api/audio-message", payload)


def backend_memorized(payload: dict) -> dict:
    return backend_post("/api/memorized", payload)


def backend_memorized_poems(payload: dict) -> dict:
    return backend_post("/api/memorized-poems", payload)


def backend_memorized_poem(payload: dict) -> dict:
    return backend_post("/api/memorized-poem", payload)


def recommendation_request_text(context: ContextTypes.DEFAULT_TYPE, ui_lang: str) -> str:
    prefs = get_prefs(context)
    required = {"language", "difficulty", "theme"}
    if required.issubset(prefs.keys()):
        return build_preference_text(prefs, ui_lang)
    return "Новая рекомендация" if ui_lang == "ru" else "New recommendation"


async def safe_edit_message(
    message: Message,
    text: str,
    parse_mode: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    try:
        await message.edit_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            logger.debug("Skipping unchanged message edit")
            return
        raise


async def safe_edit_query_message(
    update: Update,
    text: str,
    parse_mode: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    query = update.callback_query
    if query is None:
        return

    try:
        await query.edit_message_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
    except BadRequest as exc:
        if "Message is not modified" in str(exc):
            logger.debug("Skipping unchanged callback message edit")
            return
        raise


async def request_and_render_recommendation(message: Message, user, context: ContextTypes.DEFAULT_TYPE, request_text: str, edit: bool = False) -> None:
    ui_lang = get_ui_lang(context, user)
    try:
        response = backend_chat(
            {
                "telegram_user_id": user.id,
                "text": request_text,
                "full_name": user.full_name or "",
                "username": user.username or "",
                "ui_language": ui_lang,
            }
        )
    except RequestException:
        logger.exception("Failed to call backend /api/chat")
        if edit:
            await safe_edit_message(message, t(ui_lang, "backend_unavailable"), reply_markup=main_menu_keyboard(ui_lang))
        else:
            await message.reply_text(t(ui_lang, "backend_unavailable"), reply_markup=main_menu_keyboard(ui_lang))
        return

    if response.get("action") == "recommendation" and isinstance(response.get("poem"), dict):
        poem = response["poem"]
        store_recommendation_state(context, poem)
        recommendation_text = format_recommendation_message(poem, ui_lang, show_text=True)
        recommendation_markup = recommendation_actions_keyboard(ui_lang, show_text=True)
        if edit:
            await safe_edit_message(message, recommendation_text, parse_mode="HTML", reply_markup=recommendation_markup)
        else:
            await message.reply_text(recommendation_text, parse_mode="HTML", reply_markup=recommendation_markup)
        return

    if response.get("action") == "no_matching_poems":
        memorized_poems = response.get("memorized_poems") or []
        if memorized_poems:
            markup = memorized_poems_keyboard(ui_lang, memorized_poems)
        else:
            markup = main_menu_keyboard(ui_lang)

        if edit:
            await safe_edit_message(message, response.get("reply_text", ""), reply_markup=markup)
        else:
            await message.reply_text(response.get("reply_text", ""), reply_markup=markup)
        return

    if edit:
        await safe_edit_message(message, response.get("reply_text", ""), reply_markup=quick_actions_keyboard(ui_lang))
    else:
        await message.reply_text(response.get("reply_text", ""), reply_markup=quick_actions_keyboard(ui_lang))


async def call_chat_and_reply(message: Message, user, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    await request_and_render_recommendation(message, user, context, text, edit=False)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ui_lang = get_ui_lang(context, update.effective_user)
    context.user_data["prefs"] = {}
    context.user_data["active_poem"] = None
    context.user_data["awaiting_memory_input"] = False
    context.user_data["show_poem_text"] = True
    await update.message.reply_text(
        t(ui_lang, "start"),
        reply_markup=main_menu_keyboard(ui_lang),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    ui_lang = get_ui_lang(context, update.effective_user)
    await update.message.reply_text(
        t(ui_lang, "help"),
        reply_markup=main_menu_keyboard(ui_lang),
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ui_lang = get_ui_lang(context, user)
    active_poem = get_active_poem(context)

    if is_memory_mode(context) and active_poem is not None:
        poem_text = str(active_poem.get("text", ""))
        errors_count, marked_user = compare_poem_with_user(poem_text, update.message.text)
        set_memory_mode(context, False)

        if errors_count > 0:
            if ui_lang == "ru":
                result_text = (
                    f"У вас есть {errors_count} ошибок.\n\n"
                    f"Оригинальный текст:\n{escape(poem_text)}\n\n"
                    f"Ваше сообщение:\n{marked_user}\n\n"
                    "Попробуйте еще раз."
                )
            else:
                result_text = (
                    f"You have {errors_count} mistakes.\n\n"
                    f"Original text:\n{escape(poem_text)}\n\n"
                    f"Your message:\n{marked_user}\n\n"
                    "Try again."
                )
            await update.message.reply_text(result_text, parse_mode="HTML", reply_markup=memory_error_keyboard(ui_lang))
            return

        try:
            backend_memorized(
                {
                    "telegram_user_id": user.id,
                    "poem_id": int(active_poem.get("id")),
                    "score": 1.0,
                    "full_name": user.full_name or "",
                    "username": user.username or "",
                }
            )
        except RequestException:
            logger.exception("Failed to call backend /api/memorized")

        await update.message.reply_text(t(ui_lang, "mem_success"), reply_markup=memory_success_keyboard(ui_lang))
        return

    await call_chat_and_reply(update.message, user, context, update.message.text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    ui_lang = get_ui_lang(context, user)
    voice = update.message.voice or update.message.audio
    if voice is None:
        await update.message.reply_text(t(ui_lang, "no_audio"))
        return

    try:
        data = backend_audio(
            {
                "telegram_user_id": user.id,
                "file_id": voice.file_id,
                "duration_seconds": getattr(voice, "duration", 0) or 0,
                "mime_type": getattr(voice, "mime_type", None) or "audio/ogg",
                "full_name": user.full_name or "",
                "username": user.username or "",
                "ui_language": ui_lang,
            }
        )
    except RequestException:
        logger.exception("Failed to call backend /api/audio-message")
        await update.message.reply_text(
            t(ui_lang, "backend_unavailable"),
            reply_markup=main_menu_keyboard(ui_lang),
        )
        return

    await update.message.reply_text(data["reply_text"], reply_markup=quick_actions_keyboard(ui_lang))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    data = query.data or ""
    prefs = get_prefs(context)
    ui_lang = get_ui_lang(context, update.effective_user)
    active_poem = get_active_poem(context)

    if data == "rec:new":
        if query.message is not None and update.effective_user is not None:
            await request_and_render_recommendation(
                query.message,
                update.effective_user,
                context,
                recommendation_request_text(context, ui_lang),
                edit=True,
            )
        return

    if data.startswith("learned:open:"):
        if query.message is None or update.effective_user is None:
            return
        poem_id_raw = data.split(":", maxsplit=2)[2]
        try:
            poem_id = int(poem_id_raw)
        except ValueError:
            return

        try:
            response = backend_memorized_poem(
                {
                    "telegram_user_id": update.effective_user.id,
                    "poem_id": poem_id,
                    "ui_language": ui_lang,
                }
            )
        except RequestException:
            logger.exception("Failed to call backend /api/memorized-poem")
            await safe_edit_query_message(
                update,
                t(ui_lang, "backend_unavailable"),
                reply_markup=main_menu_keyboard(ui_lang),
            )
            return

        if response.get("action") == "memorized_poem_selected" and isinstance(response.get("poem"), dict):
            poem = response["poem"]
            store_recommendation_state(context, poem)
            await safe_edit_query_message(
                update,
                format_recommendation_message(poem, ui_lang, show_text=True),
                parse_mode="HTML",
                reply_markup=recommendation_actions_keyboard(ui_lang, show_text=True),
            )
            return

        await safe_edit_query_message(
            update,
            response.get("reply_text", ""),
            reply_markup=main_menu_keyboard(ui_lang),
        )
        return

    if data == "rec:toggle":
        if active_poem is None:
            await query.answer(t(ui_lang, "memory_no_poem"), show_alert=True)
            return
        next_show = not current_show_poem_text(context)
        set_show_poem_text(context, next_show)
        await safe_edit_query_message(
            update,
            format_recommendation_message(active_poem, ui_lang, show_text=next_show),
            parse_mode="HTML",
            reply_markup=recommendation_actions_keyboard(ui_lang, show_text=next_show),
        )
        return

    if data == "rec:memory":
        if active_poem is None:
            await query.answer(t(ui_lang, "memory_no_poem"), show_alert=True)
            return
        set_memory_mode(context, True)
        await safe_edit_query_message(update, t(ui_lang, "memory_prompt"))
        return

    if data == "mem:retry":
        if active_poem is None:
            await query.answer(t(ui_lang, "memory_no_poem"), show_alert=True)
            return
        set_memory_mode(context, True)
        await safe_edit_query_message(update, t(ui_lang, "memory_prompt"))
        return

    if data == "mem:back":
        if active_poem is None:
            await query.answer(t(ui_lang, "memory_no_poem"), show_alert=True)
            return
        set_memory_mode(context, False)
        show_text = current_show_poem_text(context)
        await safe_edit_query_message(
            update,
            format_recommendation_message(active_poem, ui_lang, show_text=show_text),
            parse_mode="HTML",
            reply_markup=recommendation_actions_keyboard(ui_lang, show_text=show_text),
        )
        return

    if data == "mem:next":
        if query.message is not None and update.effective_user is not None:
            await request_and_render_recommendation(
                query.message,
                update.effective_user,
                context,
                recommendation_request_text(context, ui_lang),
                edit=True,
            )
        return

    if data == "menu:toggle_lang":
        new_lang = "ru" if ui_lang == "en" else "en"
        context.user_data["ui_lang"] = new_lang
        if active_poem is not None:
            show_text = current_show_poem_text(context)
            await safe_edit_query_message(
                update,
                format_recommendation_message(active_poem, new_lang, show_text=show_text),
                parse_mode="HTML",
                reply_markup=recommendation_actions_keyboard(new_lang, show_text=show_text),
            )
            return
        await safe_edit_query_message(
            update,
            f"{t(new_lang, 'lang_switched')}\n\n{t(new_lang, 'menu_title')}",
            reply_markup=main_menu_keyboard(new_lang),
        )
        return

    if data == "menu:main":
        set_memory_mode(context, False)
        await safe_edit_query_message(
            update,
            t(ui_lang, "menu_title"),
            reply_markup=main_menu_keyboard(ui_lang),
        )
        return

    if data == "menu:help":
        await safe_edit_query_message(
            update,
            t(ui_lang, "mini_help_text"),
            reply_markup=main_menu_keyboard(ui_lang),
        )
        return

    if data == "menu:voice":
        await safe_edit_query_message(
            update,
            t(ui_lang, "voice_help_text"),
            reply_markup=main_menu_keyboard(ui_lang),
        )
        return

    if data == "menu:learned":
        if update.effective_user is None:
            return
        try:
            response = backend_memorized_poems(
                {
                    "telegram_user_id": update.effective_user.id,
                    "ui_language": ui_lang,
                }
            )
        except RequestException:
            logger.exception("Failed to call backend /api/memorized-poems")
            await safe_edit_query_message(
                update,
                t(ui_lang, "backend_unavailable"),
                reply_markup=main_menu_keyboard(ui_lang),
            )
            return

        await safe_edit_query_message(
            update,
            response.get("reply_text", ""),
            reply_markup=memorized_poems_keyboard(ui_lang, response.get("memorized_poems") or []),
        )
        return

    if data == "menu:recommend":
        prefs.clear()
        await safe_edit_query_message(
            update,
            recommendation_prompt_text(prefs, ui_lang),
            reply_markup=recommendation_keyboard(prefs, ui_lang),
        )
        return

    if data == "menu:memory":
        if active_poem is None:
            await query.answer(t(ui_lang, "memory_no_poem"), show_alert=True)
            return
        set_memory_mode(context, True)
        await safe_edit_query_message(update, t(ui_lang, "memory_prompt"))
        return

    if data == "pref:reset":
        prefs.clear()
        await safe_edit_query_message(
            update,
            recommendation_prompt_text(prefs, ui_lang),
            reply_markup=recommendation_keyboard(prefs, ui_lang),
        )
        return

    if data.startswith("pref:lang:"):
        prefs["language"] = data.split(":", maxsplit=2)[2]
        await safe_edit_query_message(
            update,
            recommendation_prompt_text(prefs, ui_lang),
            reply_markup=recommendation_keyboard(prefs, ui_lang),
        )
        return

    if data.startswith("pref:diff:"):
        prefs["difficulty"] = data.split(":", maxsplit=2)[2]
        await safe_edit_query_message(
            update,
            recommendation_prompt_text(prefs, ui_lang),
            reply_markup=recommendation_keyboard(prefs, ui_lang),
        )
        return

    if data.startswith("pref:theme:"):
        prefs["theme"] = data.split(":", maxsplit=2)[2]
        await safe_edit_query_message(
            update,
            recommendation_prompt_text(prefs, ui_lang),
            reply_markup=recommendation_keyboard(prefs, ui_lang),
        )
        return

    if data == "pref:submit":
        required = {"language", "difficulty", "theme"}
        if not required.issubset(prefs.keys()):
            await query.answer(t(ui_lang, "required_alert"), show_alert=True)
            return
        if query.message is not None and update.effective_user is not None:
            await request_and_render_recommendation(
                query.message,
                update.effective_user,
                context,
                build_preference_text(prefs, ui_lang),
                edit=True,
            )
        return


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception while processing update", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message is not None:
        ui_lang = get_ui_lang(context, update.effective_user)
        await update.effective_message.reply_text(t(ui_lang, "unexpected_error"))


if __name__ == "__main__":
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_error_handler(on_error)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
