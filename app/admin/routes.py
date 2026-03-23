from __future__ import annotations

from datetime import datetime
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, select
import secrets

from app.core.config import settings
from app.core.db import get_session
from app.models.tables import AudioSubmission, Poem

router = APIRouter(tags=["admin"])
security = HTTPBasic()


LANGUAGES = ["ru", "en", "mixed"]
DIFFICULTIES = ["easy", "medium", "hard"]
THEMES = ["love", "nature", "freedom", "life_choice", "mixed"]


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    username_ok = secrets.compare_digest(credentials.username, settings.admin_username)
    password_ok = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
    return credentials.username


def normalize_poem_text(value: str) -> str:
    lines = [line.rstrip() for line in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line.strip())


def first_line_from_text(value: str) -> str:
    for line in value.split("\n"):
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def option_tags(values: list[str], selected: str) -> str:
    return "".join(
        f'<option value="{escape(v)}" {"selected" if v == selected else ""}>{escape(v)}</option>' for v in values
    )


def render_layout(content: str) -> HTMLResponse:
    return HTMLResponse(
        f"""
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Poetry Admin</title>
          <style>
            body {{ font-family: Arial, sans-serif; margin: 32px; background: #f6f7fb; color: #111; }}
            .container {{ max-width: 1100px; margin: 0 auto; }}
            .card {{ background: white; border-radius: 14px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,.08); }}
            h1, h2, h3 {{ margin-top: 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border-bottom: 1px solid #e7e7e7; padding: 10px; text-align: left; vertical-align: top; }}
            input, select, textarea {{ width: 100%; padding: 10px; border: 1px solid #cfd5df; border-radius: 8px; margin-top: 6px; margin-bottom: 14px; box-sizing: border-box; }}
            textarea {{ min-height: 220px; font-family: Consolas, monospace; }}
            .row {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }}
            .actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
            .btn {{ display:inline-block; padding:10px 14px; border-radius:10px; border:none; background:#111827; color:#fff; text-decoration:none; cursor:pointer; }}
            .btn.secondary {{ background:#4b5563; }}
            .btn.danger {{ background:#b91c1c; }}
            pre {{ white-space: pre-wrap; background: #f3f4f6; padding: 14px; border-radius: 10px; }}
            .muted {{ color:#6b7280; font-size: 14px; }}
          </style>
        </head>
        <body><div class="container">{content}</div></body>
        </html>
        """
    )


@router.get("/", response_class=HTMLResponse)
def admin_home(
    request: Request,
    session: Session = Depends(get_session),
    _: str = Depends(require_admin),
) -> HTMLResponse:
    poems = session.exec(select(Poem).order_by(Poem.updated_at.desc())).all()
    audio_items = session.exec(select(AudioSubmission).order_by(AudioSubmission.created_at.desc())).all()[:20]
    poem_rows = "".join(
        f"<tr><td>{poem.id}</td><td>{escape(poem.title)}</td><td>{escape(poem.author)}</td><td>{escape(poem.language)}</td>"
        f"<td>{escape(poem.difficulty)}</td><td>{escape(poem.theme)}</td><td>{'yes' if poem.is_active else 'no'}</td>"
        f"<td><a class='btn secondary' href='/admin/poems/{poem.id}/edit'>Edit</a></td></tr>"
        for poem in poems
    ) or "<tr><td colspan='8'>No poems yet.</td></tr>"
    audio_rows = "".join(
        f"<tr><td>{item.id}</td><td>{item.telegram_user_id}</td><td>{escape(item.file_id)}</td><td>{item.duration_seconds}s</td><td>{escape(item.status)}</td><td>{item.created_at}</td></tr>"
        for item in audio_items
    ) or "<tr><td colspan='6'>No audio submissions yet.</td></tr>"
    return render_layout(
        f"""
        <div class='card'>
          <h1>Poetry Admin Panel</h1>
          <p class='muted'>Manage poem catalog without AI services. Basic Auth protected.</p>
          <div class='actions'>
            <a class='btn' href='/admin/poems/new'>Add poem</a>
            <a class='btn secondary' href='/docs'>API docs</a>
            <a class='btn secondary' href='/health'>Health</a>
          </div>
        </div>

        <div class='card'>
          <h2>Poems</h2>
          <table>
            <thead><tr><th>ID</th><th>Title</th><th>Author</th><th>Lang</th><th>Difficulty</th><th>Theme</th><th>Active</th><th></th></tr></thead>
            <tbody>{poem_rows}</tbody>
          </table>
        </div>

        <div class='card'>
          <h2>Recent audio submissions</h2>
          <p class='muted'>Audio is accepted and logged, but not transcribed automatically in this non-AI version.</p>
          <table>
            <thead><tr><th>ID</th><th>User</th><th>Telegram file_id</th><th>Duration</th><th>Status</th><th>Created</th></tr></thead>
            <tbody>{audio_rows}</tbody>
          </table>
        </div>
        """
    )


@router.get("/poems/new", response_class=HTMLResponse)
def new_poem_form(_: str = Depends(require_admin)) -> HTMLResponse:
    return poem_form_page(title="", author="", language="ru", difficulty="medium", theme="mixed", source_hint="public domain / educational use", notes="", text="", poem_id=None, is_active=True)


@router.get("/poems/{poem_id}/edit", response_class=HTMLResponse)
def edit_poem_form(poem_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)) -> HTMLResponse:
    poem = session.get(Poem, poem_id)
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")
    return poem_form_page(
        title=poem.title,
        author=poem.author,
        language=poem.language,
        difficulty=poem.difficulty,
        theme=poem.theme,
        source_hint=poem.source_hint,
        notes=poem.notes,
        text=poem.text,
        poem_id=poem.id,
        is_active=poem.is_active,
    )


@router.post("/poems")
def create_poem(
    title: str = Form(...),
    author: str = Form(...),
    language: str = Form(...),
    difficulty: str = Form(...),
    theme: str = Form(...),
    source_hint: str = Form("public domain / educational use"),
    notes: str = Form(""),
    text: str = Form(...),
    is_active: bool = Form(False),
    session: Session = Depends(get_session),
    _: str = Depends(require_admin),
):
    normalized_text = normalize_poem_text(text)
    poem = Poem(
        title=title.strip(),
        author=author.strip(),
        language=language,
        difficulty=difficulty,
        theme=theme,
        text=normalized_text,
        first_line=first_line_from_text(normalized_text),
        source_hint=source_hint.strip(),
        notes=notes.strip(),
        is_active=is_active,
    )
    session.add(poem)
    session.commit()
    return RedirectResponse(url="/admin/", status_code=303)


@router.post("/poems/{poem_id}")
def update_poem(
    poem_id: int,
    title: str = Form(...),
    author: str = Form(...),
    language: str = Form(...),
    difficulty: str = Form(...),
    theme: str = Form(...),
    source_hint: str = Form("public domain / educational use"),
    notes: str = Form(""),
    text: str = Form(...),
    is_active: bool = Form(False),
    session: Session = Depends(get_session),
    _: str = Depends(require_admin),
):
    poem = session.get(Poem, poem_id)
    if not poem:
        raise HTTPException(status_code=404, detail="Poem not found")
    normalized_text = normalize_poem_text(text)
    poem.title = title.strip()
    poem.author = author.strip()
    poem.language = language
    poem.difficulty = difficulty
    poem.theme = theme
    poem.source_hint = source_hint.strip()
    poem.notes = notes.strip()
    poem.text = normalized_text
    poem.first_line = first_line_from_text(normalized_text)
    poem.is_active = is_active
    poem.updated_at = datetime.utcnow()
    session.add(poem)
    session.commit()
    return RedirectResponse(url="/admin/", status_code=303)


@router.post("/poems/{poem_id}/delete")
def delete_poem(poem_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    poem = session.get(Poem, poem_id)
    if poem:
        session.delete(poem)
        session.commit()
    return RedirectResponse(url="/admin/", status_code=303)


def poem_form_page(*, title: str, author: str, language: str, difficulty: str, theme: str, source_hint: str, notes: str, text: str, poem_id: int | None, is_active: bool) -> HTMLResponse:
    normalized_preview = normalize_poem_text(text)
    action_url = f"/admin/poems/{poem_id}" if poem_id else "/admin/poems"
    page_title = "Edit poem" if poem_id else "Add poem"
    delete_block = (
        f"<form method='post' action='/admin/poems/{poem_id}/delete' onsubmit=\"return confirm('Delete this poem?')\"><button class='btn danger' type='submit'>Delete</button></form>"
        if poem_id
        else ""
    )
    return render_layout(
        f"""
        <div class='card'>
          <h1>{page_title}</h1>
          <div class='actions'>
            <a class='btn secondary' href='/admin/'>Back to admin</a>
          </div>
        </div>
        <div class='card'>
          <form method='post' action='{action_url}'>
            <label>Title<input name='title' value='{escape(title)}' required></label>
            <label>Author<input name='author' value='{escape(author)}' required></label>
            <div class='row'>
              <label>Language<select name='language'>{option_tags(LANGUAGES, language)}</select></label>
              <label>Difficulty<select name='difficulty'>{option_tags(DIFFICULTIES, difficulty)}</select></label>
              <label>Theme<select name='theme'>{option_tags(THEMES, theme)}</select></label>
            </div>
            <label>Source hint<input name='source_hint' value='{escape(source_hint)}'></label>
            <label>Notes<input name='notes' value='{escape(notes)}'></label>
            <label>Poem text<textarea name='text' required>{escape(text)}</textarea></label>
            <label><input type='checkbox' name='is_active' {'checked' if is_active else ''} style='width:auto; margin-right:8px;'>Active in recommendations</label>
            <div class='actions'>
              <button class='btn' type='submit'>Save</button>
              {delete_block}
            </div>
          </form>
        </div>
        <div class='card'>
          <h2>Formatting preview</h2>
          <p class='muted'>The system removes empty lines and automatically derives the first line for revision prompts.</p>
          <pre>{escape(normalized_preview)}</pre>
          <p><strong>Detected first line:</strong> {escape(first_line_from_text(normalized_preview))}</p>
        </div>
        """
    )
