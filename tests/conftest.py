"""Shared fixtures and configuration for tests."""

import os
from datetime import datetime

import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.core.config import settings
from app.models.tables import AudioSubmission, Poem, RecommendationEvent, RevisionEvent, UserPreference, UserProfile


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session) -> UserProfile:
    """Create a test user."""
    user = UserProfile(
        telegram_user_id=123456789,
        full_name="Test User",
        username="testuser",
        language_pref="en",
        difficulty_pref="medium",
        theme_pref="nature",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_poem")
def test_poem_fixture(session: Session) -> Poem:
    """Create a test poem."""
    poem = Poem(
        title="The Road Not Taken",
        author="Robert Frost",
        language="en",
        difficulty="medium",
        theme="life_choice",
        text="Two roads diverged in a yellow wood,\nAnd sorry I could not travel both...",
        first_line="Two roads diverged in a yellow wood,",
        is_active=True,
    )
    session.add(poem)
    session.commit()
    session.refresh(poem)
    return poem


@pytest.fixture(name="test_user_ru")
def test_user_ru_fixture(session: Session) -> UserProfile:
    """Create a test Russian-speaking user."""
    user = UserProfile(
        telegram_user_id=987654321,
        full_name="Иван Петров",
        username="ivan_petrov",
        language_pref="ru",
        difficulty_pref="easy",
        theme_pref="love",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="test_poem_ru")
def test_poem_ru_fixture(session: Session) -> Poem:
    """Create a test Russian poem."""
    poem = Poem(
        title="Парус",
        author="М.Ю. Лермонтов",
        language="ru",
        difficulty="medium",
        theme="freedom",
        text="Белеет парус одинокий\nВ тумане моря голубом!...",
        first_line="Белеет парус одинокий",
        is_active=True,
    )
    session.add(poem)
    session.commit()
    session.refresh(poem)
    return poem
