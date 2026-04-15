"""Service for handling user reminders about inactive learners."""

from datetime import datetime, timedelta, timezone
import logging

from sqlmodel import Session, select

from app.models.tables import UserProfile

logger = logging.getLogger(__name__)

# Constants
INACTIVITY_DAYS = 3
REMINDER_HOUR = 12  # 12:00 noon


def get_inactive_users(session: Session, days: int = INACTIVITY_DAYS) -> list[UserProfile]:
    """
    Get users who haven't been active for the specified number of days.
    
    Args:
        session: Database session
        days: Number of days of inactivity to check for (default: 3)
        
    Returns:
        List of inactive UserProfile objects
    """
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    inactive_users = session.exec(
        select(UserProfile).where(UserProfile.last_active_at < cutoff_time)
    ).all()
    
    return inactive_users


def get_reminder_text(ui_language: str = "en") -> tuple[str, str]:
    """
    Get reminder message text based on user's preferred language.
    
    Args:
        ui_language: User's UI language preference ('ru' or 'en')
        
    Returns:
        Tuple of (title, message_text)
    """
    
    if ui_language == "ru":
        title = "📖 Напоминание о стихотворениях"
        message = (
            "Привет! 🎭\n\n"
            "Я заметил, что вы не проявляли активности последние 3 дня.\n\n"
            "Давайте вернёмся к изучению стихотворений! "
            "Используйте боту, чтобы:\n"
            "• Получить новую рекомендацию (/start)\n"
            "• Проверить память по уже выученным стихам\n"
            "• Просмотреть свой прогресс\n\n"
            "Помните, регулярная практика — ключ к успеху! 💪"
        )
    else:
        title = "📖 Poetry Learning Reminder"
        message = (
            "Hi there! 🎭\n\n"
            "I noticed you haven't been active for the last 3 days.\n\n"
            "Let's get back to learning poems! Use me to:\n"
            "• Get a new poem recommendation (/start)\n"
            "• Practice memory checks on poems you know\n"
            "• View your learning progress\n\n"
            "Remember, consistent practice is key to success! 💪"
        )
    
    return title, message


def format_reminder_message(ui_language: str = "en") -> str:
    """
    Format a complete reminder message for users.
    
    Args:
        ui_language: User's UI language preference
        
    Returns:
        Formatted message string
    """
    _, message = get_reminder_text(ui_language)
    return message
