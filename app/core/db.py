from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    from app.models.tables import AudioSubmission, Poem, RecommendationEvent, RevisionEvent, UserPreference, UserProfile

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        if session.query(Poem).count() == 0:
            from app.services.seed_data import seed_poems

            seed_poems(session)


def get_session():
    with Session(engine) as session:
        yield session
