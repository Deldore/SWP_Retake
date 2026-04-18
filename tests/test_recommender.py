"""Tests for app.services.recommender module."""

from datetime import datetime, timedelta

import pytest
from sqlmodel import Session

from app.models.tables import Poem, RecommendationEvent, RevisionEvent, UserProfile
from app.services.recommender import (
    infer_preferences,
    learner_profile_summary,
    mark_poem_memorized,
    memorized_poems,
    upsert_user,
)


class TestUpsertUser:
    """Tests for upsert_user function."""

    def test_create_new_user(self, session: Session):
        """Test creating a new user."""
        user = upsert_user(session, 123456789, "John Doe", "johndoe")

        assert user.telegram_user_id == 123456789
        assert user.full_name == "John Doe"
        assert user.username == "johndoe"
        assert user.last_active_at is not None

    def test_update_existing_user(self, session: Session, test_user: UserProfile):
        """Test updating an existing user."""
        old_timestamp = test_user.last_active_at

        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.01)

        updated_user = upsert_user(
            session, test_user.telegram_user_id, "New Name", "newusername"
        )

        assert updated_user.full_name == "New Name"
        assert updated_user.username == "newusername"
        assert updated_user.last_active_at > old_timestamp

    def test_upsert_user_preserves_preferences(
        self, session: Session, test_user: UserProfile
    ):
        """Test that upsert_user preserves user preferences."""
        original_language_pref = test_user.language_pref

        updated_user = upsert_user(
            session, test_user.telegram_user_id, "Updated", "updated"
        )

        assert updated_user.language_pref == original_language_pref


class TestInferPreferences:
    """Tests for infer_preferences function."""

    def test_infer_english_language(self):
        """Test inferring English language preference."""
        prefs = infer_preferences("I love English poems")
        assert prefs.get("language_pref") == "en"

    def test_infer_russian_language(self):
        """Test inferring Russian language preference."""
        prefs = infer_preferences("Люблю русские стихи")
        assert prefs.get("language_pref") == "ru"

    def test_infer_difficulty_easy(self):
        """Test inferring easy difficulty."""
        prefs = infer_preferences("I want something easy and short")
        assert prefs.get("difficulty_pref") == "easy"

    def test_infer_difficulty_hard(self):
        """Test inferring hard difficulty."""
        prefs = infer_preferences("Give me a hard and complex poem")
        assert prefs.get("difficulty_pref") == "hard"

    def test_infer_theme_nature(self):
        """Test inferring nature theme."""
        prefs = infer_preferences("I like poems about nature and snow")
        assert prefs.get("theme_pref") == "nature"

    def test_infer_theme_love(self):
        """Test inferring love theme."""
        prefs = infer_preferences("Show me a love poem")
        assert prefs.get("theme_pref") == "love"


class TestLearnerProfileSummary:
    """Tests for learner_profile_summary function."""

    def test_empty_profile_summary(self, session: Session, test_user: UserProfile):
        """Test summary for user with no history."""
        summary = learner_profile_summary(session, test_user.telegram_user_id)

        assert summary["recommendations_total"] == 0
        assert summary["memorized_total"] == 0
        assert summary["average_revision_score"] == 0.0

    def test_profile_summary_with_recommendations(
        self, session: Session, test_user: UserProfile, test_poem: Poem
    ):
        """Test summary with recommendation events."""
        event = RecommendationEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            outcome="recommended",
        )
        session.add(event)
        session.commit()

        summary = learner_profile_summary(session, test_user.telegram_user_id)
        assert summary["recommendations_total"] == 1
        assert summary["memorized_total"] == 0

    def test_profile_summary_with_memorized_poems(
        self, session: Session, test_user: UserProfile, test_poem: Poem
    ):
        """Test summary with memorized poems."""
        event = RecommendationEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            outcome="memorized",
            score=0.95,
        )
        session.add(event)
        session.commit()

        summary = learner_profile_summary(session, test_user.telegram_user_id)
        assert summary["recommendations_total"] == 1
        assert summary["memorized_total"] == 1

    def test_profile_summary_average_revision_score(
        self, session: Session, test_user: UserProfile, test_poem: Poem
    ):
        """Test average revision score calculation."""
        revision1 = RevisionEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            score=0.8,
        )
        revision2 = RevisionEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            score=0.9,
        )
        session.add(revision1)
        session.add(revision2)
        session.commit()

        summary = learner_profile_summary(session, test_user.telegram_user_id)
        assert summary["average_revision_score"] == 0.85


class TestMemorizedPoems:
    """Tests for memorized_poems function."""

    def test_no_memorized_poems(self, session: Session, test_user: UserProfile):
        """Test getting memorized poems for user with none."""
        poems = memorized_poems(session, test_user.telegram_user_id)
        assert len(poems) == 0

    def test_get_memorized_poems(
        self, session: Session, test_user: UserProfile, test_poem: Poem
    ):
        """Test getting memorized poems."""
        event = RecommendationEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            outcome="memorized",
        )
        session.add(event)
        session.commit()

        result = memorized_poems(session, test_user.telegram_user_id)
        assert len(result) == 1
        assert result[0].id == test_poem.id

    def test_memorized_poems_excludes_non_memorized(
        self, session: Session, test_user: UserProfile, test_poem: Poem
    ):
        """Test that non-memorized poems are excluded."""
        event1 = RecommendationEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            outcome="recommended",
        )
        event2 = RecommendationEvent(
            telegram_user_id=test_user.telegram_user_id,
            poem_id=test_poem.id,
            outcome="memorized",
        )
        session.add(event1)
        session.add(event2)
        session.commit()

        result = memorized_poems(session, test_user.telegram_user_id)
        # Should only return the memorized one
        assert len(result) == 1
