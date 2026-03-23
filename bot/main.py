import logging
from urllib.parse import urlparse, urlunparse

import requests
from requests import RequestException
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.core.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Get recommendation", callback_data="menu:recommend")],
            [InlineKeyboardButton("Memory check", callback_data="menu:memory")],
            [InlineKeyboardButton("Voice message help", callback_data="menu:voice")],
            [InlineKeyboardButton("Help", callback_data="menu:help")],
        ]
    )


def quick_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("New recommendation", callback_data="menu:recommend")],
            [InlineKeyboardButton("Memory check", callback_data="menu:memory")],
            [InlineKeyboardButton("Main menu", callback_data="menu:main")],
        ]
    )


def recommendation_keyboard(prefs: dict[str, str]) -> InlineKeyboardMarkup:
    language = prefs.get("language")
    difficulty = prefs.get("difficulty")
    theme = prefs.get("theme")

    def mark(current: str | None, value: str, label: str) -> str:
        return f"[x] {label}" if current == value else label

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(mark(language, "ru", "Russian"), callback_data="pref:lang:ru"),
                InlineKeyboardButton(mark(language, "en", "English"), callback_data="pref:lang:en"),
                InlineKeyboardButton(mark(language, "mixed", "Mixed"), callback_data="pref:lang:mixed"),
            ],
            [
                InlineKeyboardButton(mark(difficulty, "easy", "Easy"), callback_data="pref:diff:easy"),
                InlineKeyboardButton(mark(difficulty, "hard", "Hard"), callback_data="pref:diff:hard"),
            ],
            [
                InlineKeyboardButton(mark(theme, "love", "Love"), callback_data="pref:theme:love"),
                InlineKeyboardButton(mark(theme, "nature", "Nature"), callback_data="pref:theme:nature"),
            ],
            [
                InlineKeyboardButton(mark(theme, "freedom", "Freedom"), callback_data="pref:theme:freedom"),
                InlineKeyboardButton(mark(theme, "life_choice", "Life choice"), callback_data="pref:theme:life_choice"),
            ],
            [
                InlineKeyboardButton("Recommend now", callback_data="pref:submit"),
                InlineKeyboardButton("Reset", callback_data="pref:reset"),
            ],
            [InlineKeyboardButton("Main menu", callback_data="menu:main")],
        ]
    )


def recommendation_prompt_text(prefs: dict[str, str]) -> str:
    language = prefs.get("language", "not selected")
    difficulty = prefs.get("difficulty", "not selected")
    theme = prefs.get("theme", "not selected")
    return (
        "Choose preferences with buttons and press 'Recommend now'.\n\n"
        f"Language: {language}\n"
        f"Difficulty: {difficulty}\n"
        f"Theme: {theme}"
    )


def build_preference_text(prefs: dict[str, str]) -> str:
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


def get_prefs(context: ContextTypes.DEFAULT_TYPE) -> dict[str, str]:
    prefs = context.user_data.get("prefs")
    if isinstance(prefs, dict):
        return prefs
    prefs = {}
    context.user_data["prefs"] = prefs
    return prefs


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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["prefs"] = {}
    await update.message.reply_text(
        "Hi! I am Poetry Bot.\n"
        "Use buttons below to get recommendations, run memory checks, and work with voice messages.",
        reply_markup=main_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - open interactive menu\n"
        "/help - show this help\n\n"
        "Recommended flow:\n"
        "1) Press 'Get recommendation'\n"
        "2) Choose language, difficulty, and theme\n"
        "3) Press 'Recommend now'\n"
        "4) Send remembered lines as text, or press 'Memory check'\n\n"
        "You can still type free text if you prefer.",
        reply_markup=main_menu_keyboard(),
    )


def backend_chat(payload: dict) -> dict:
    return backend_post("/api/chat", payload)


def backend_audio(payload: dict) -> dict:
    return backend_post("/api/audio-message", payload)


async def call_chat_and_reply(message: Message, user, text: str) -> None:
    try:
        data = backend_chat(
            {
                "telegram_user_id": user.id,
                "text": text,
                "full_name": user.full_name or "",
                "username": user.username or "",
            }
        )
    except RequestException:
        logger.exception("Failed to call backend /api/chat")
        await message.reply_text(
            "Backend is temporarily unavailable. Please make sure API is running and try again.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.reply_text(data["reply_text"], parse_mode="Markdown", reply_markup=quick_actions_keyboard())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await call_chat_and_reply(update.message, user, update.message.text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    voice = update.message.voice or update.message.audio
    if voice is None:
        await update.message.reply_text("I received no audio.")
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
            }
        )
    except RequestException:
        logger.exception("Failed to call backend /api/audio-message")
        await update.message.reply_text(
            "Backend is temporarily unavailable. Please make sure API is running and try again.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await update.message.reply_text(data["reply_text"], parse_mode="Markdown", reply_markup=quick_actions_keyboard())


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    data = query.data or ""
    prefs = get_prefs(context)

    if data == "menu:main":
        await query.edit_message_text(
            "Main menu. Choose an action:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu:help":
        await query.edit_message_text(
            "Use 'Get recommendation' to build preferences through buttons.\n"
            "Use 'Memory check' when you want a revision prompt.\n"
            "You can still send free text or voice at any time.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu:voice":
        await query.edit_message_text(
            "Send a voice message directly in chat.\n"
            "I will save it and ask you to send poem lines as text for memorization checking.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu:recommend":
        prefs.clear()
        await query.edit_message_text(
            recommendation_prompt_text(prefs),
            reply_markup=recommendation_keyboard(prefs),
        )
        return

    if data == "menu:memory":
        if query.message is not None and update.effective_user is not None:
            await query.edit_message_text("Preparing memory check prompt...")
            await call_chat_and_reply(query.message, update.effective_user, "Проверка памяти")
        return

    if data == "pref:reset":
        prefs.clear()
        await query.edit_message_text(
            recommendation_prompt_text(prefs),
            reply_markup=recommendation_keyboard(prefs),
        )
        return

    if data.startswith("pref:lang:"):
        prefs["language"] = data.split(":", maxsplit=2)[2]
        await query.edit_message_text(
            recommendation_prompt_text(prefs),
            reply_markup=recommendation_keyboard(prefs),
        )
        return

    if data.startswith("pref:diff:"):
        prefs["difficulty"] = data.split(":", maxsplit=2)[2]
        await query.edit_message_text(
            recommendation_prompt_text(prefs),
            reply_markup=recommendation_keyboard(prefs),
        )
        return

    if data.startswith("pref:theme:"):
        prefs["theme"] = data.split(":", maxsplit=2)[2]
        await query.edit_message_text(
            recommendation_prompt_text(prefs),
            reply_markup=recommendation_keyboard(prefs),
        )
        return

    if data == "pref:submit":
        required = {"language", "difficulty", "theme"}
        if not required.issubset(prefs.keys()):
            await query.answer("Please select language, difficulty, and theme first.", show_alert=True)
            return
        if query.message is not None and update.effective_user is not None:
            await query.edit_message_text("Preparing recommendation...")
            await call_chat_and_reply(query.message, update.effective_user, build_preference_text(prefs))
        return


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("Unhandled exception while processing update", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message is not None:
        await update.effective_message.reply_text("Unexpected error occurred. Please try again later.")


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
