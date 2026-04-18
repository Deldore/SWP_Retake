"""Tests for app.services.reminder module."""

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from app.models.tables import UserProfile
from app.services.reminder import format_reminder_message, get_inactive_users, get_reminder_text


class TestGetInactiveUsers:
    """Tests for get_inactive_users function."""

    def test_no_inactive_users(self, session: Session, test_user: UserProfile):
        """Test when all users are active."""
        inactive = get_inactive_users(session, days=3)
        assert len(inactive) == 0

    def test_find_inactive_users(self, session: Session):
        """Test finding inactive users."""
        # Create user inactive for 5 days
        old_date = datetime.utcnow() - timedelta(days=5)
        user = UserProfile(
            telegram_user_id=111111,
            full_name="Inactive User",
            username="inactive",
            last_active_at=old_date,
        )
        session.add(user)
        session.commit()

        inactive = get_inactive_users(session, days=3)
        assert len(inactive) == 1
        assert inactive[0].telegram_user_id == 111111

    def test_exclude_recently_active_users(self, session: Session):
        """Test that recently active users are not included."""
        # Create user inactive for only 1 day
        old_date = datetime.utcnow() - timedelta(days=1)
        user = UserProfile(
            telegram_user_id=222222,
            full_name="Active User",
            username="active",
            last_active_at=old_date,
        )
        session.add(user)
        session.commit()

        inactive = get_inactive_users(session, days=3)
        assert len(inactive) == 0

    def test_custom_inactivity_threshold(self, session: Session):
        """Test with custom inactivity threshold."""
        # Create user inactive for 2 days
        old_date = datetime.utcnow() - timedelta(days=2)
        user = UserProfile(
            telegram_user_id=333333,
            full_name="Test User",
            username="test",
            last_active_at=old_date,
        )
        session.add(user)
        session.commit()

        # With 3-day threshold, should not be found
        inactive_3days = get_inactive_users(session, days=3)
        assert len(inactive_3days) == 0

        # With 1-day threshold, should be found
        inactive_1day = get_inactive_users(session, days=1)
        assert len(inactive_1day) == 1


class TestGetReminderText:
    """Tests for get_reminder_text function."""

    def test_english_reminder_text(self):
        """Test English reminder text."""
        title, message = get_reminder_text("en")

        assert title == "📖 Poetry Learning Reminder"
        assert "haven't been active" in message
        assert "/start" in message
        assert len(message) > 0

    def test_russian_reminder_text(self):
        """Test Russian reminder text."""
        title, message = get_reminder_text("ru")

        assert title == "📖 Напоминание о стихотворениях"
        assert "не проявляли активности" in message
        assert "/start" in message
        assert len(message) > 0

    def test_default_language_is_english(self):
        """Test that default language is English."""
        title, message = get_reminder_text("unknown")

        assert title == "📖 Poetry Learning Reminder"
        assert "haven't been active" in message


class TestFormatReminderMessage:
    """Tests for format_reminder_message function."""

    def test_english_message_formatting(self):
        """Test English message formatting."""
        message = format_reminder_message("en")

        assert "haven't been active" in message
        assert "3 days" in message
        assert "/start" in message

    def test_russian_message_formatting(self):
        """Test Russian message formatting."""
        message = format_reminder_message("ru")

        assert "не проявляли активности" in message
        assert "3 дня" in message
        assert "стихотворений" in message
        assert "/start" in message

    def test_message_contains_call_to_action(self):
        """Test that message contains call to action."""
        message_en = format_reminder_message("en")
        message_ru = format_reminder_message("ru")

        assert "/start" in message_en
        assert "/start" in message_ru
        assert "recommendation" in message_en or "poem" in message_en
        assert "рекомендацию" in message_ru or "стихотворений" in message_ru
