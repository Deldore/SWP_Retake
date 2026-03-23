from sqlmodel import Session

from app.models.tables import Poem


POEMS = [
    {
        "title": "The Road Not Taken",
        "author": "Robert Frost",
        "language": "en",
        "difficulty": "medium",
        "theme": "life_choice",
        "first_line": "Two roads diverged in a yellow wood,",
        "text": "Two roads diverged in a yellow wood,\nAnd sorry I could not travel both\nAnd be one traveler, long I stood\nAnd looked down one as far as I could\nTo where it bent in the undergrowth;",
    },
    {
        "title": "Stopping by Woods on a Snowy Evening",
        "author": "Robert Frost",
        "language": "en",
        "difficulty": "easy",
        "theme": "nature",
        "first_line": "Whose woods these are I think I know.",
        "text": "Whose woods these are I think I know.\nHis house is in the village though;\nHe will not see me stopping here\nTo watch his woods fill up with snow.",
    },
    {
        "title": "Я вас любил",
        "author": "Александр Пушкин",
        "language": "ru",
        "difficulty": "easy",
        "theme": "love",
        "first_line": "Я вас любил: любовь еще, быть может,",
        "text": "Я вас любил: любовь еще, быть может,\nВ душе моей угасла не совсем;\nНо пусть она вас больше не тревожит;\nЯ не хочу печалить вас ничем.",
    },
    {
        "title": "Парус",
        "author": "Михаил Лермонтов",
        "language": "ru",
        "difficulty": "medium",
        "theme": "freedom",
        "first_line": "Белеет парус одинокой",
        "text": "Белеет парус одинокой\nВ тумане моря голубом!..\nЧто ищет он в стране далекой?\nЧто кинул он в краю родном?..",
    },
    {
        "title": "Sonnet 18",
        "author": "William Shakespeare",
        "language": "en",
        "difficulty": "hard",
        "theme": "love",
        "first_line": "Shall I compare thee to a summer’s day?",
        "text": "Shall I compare thee to a summer’s day?\nThou art more lovely and more temperate:\nRough winds do shake the darling buds of May,\nAnd summer’s lease hath all too short a date;",
    },
    {
        "title": "Зимнее утро",
        "author": "Александр Пушкин",
        "language": "ru",
        "difficulty": "medium",
        "theme": "nature",
        "first_line": "Мороз и солнце; день чудесный!",
        "text": "Мороз и солнце; день чудесный!\nЕще ты дремлешь, друг прелестный —\nПора, красавица, проснись:\nОткрой сомкнуты негой взоры",
    },
]


def seed_poems(session: Session) -> None:
    for poem in POEMS:
        session.add(Poem(**poem))
    session.commit()
