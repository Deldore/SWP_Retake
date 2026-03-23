# Poetry: A Conversational Recommender System

Telegram bot + FastAPI backend for recommending classic poems in English and Russian, checking memorization, and managing the poem catalog through a built-in admin panel.

## What changed in this version

This version deliberately **does not use OpenAI API, neural networks, or any other AI service**.

- recommendation logic is rule-based
- memorization check is based on token overlap
- text messages are processed automatically
- audio messages are **accepted and recorded** in learner history, but not transcribed automatically
- an **admin panel** is included for adding, formatting, editing, and activating poems

This still satisfies the coursework requirement to accept both text and audio messages, while keeping the implementation deterministic and fully reproducible.

## Tech stack

- **Backend:** FastAPI + SQLModel + SQLite
- **Frontend:** Telegram Bot (`python-telegram-bot`)
- **Admin panel:** server-rendered FastAPI pages + Basic Auth
- **Deployment:** Docker + Docker Compose

## Features

1. Elicit user preferences by chat
2. Store user history and learner profile
3. Recommend a poem by language, difficulty, and theme
4. Check memorization from text recall
5. Record recommendation outcomes
6. Track audio submissions in learner history
7. Manage poem catalog from `/admin/`

## Bot UX

The Telegram bot supports both free text and inline-button navigation.

- interactive menu via `/start`
- preference builder with buttons: language, difficulty, theme
- one-tap memory check prompt
- quick actions after each response (new recommendation, memory check, main menu)
- voice-message shortcut flow with guidance

## Admin panel

Open:

```text
http://localhost:8000/admin/
```

Credentials are configured in `.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

The admin panel supports:

- adding new poems
- editing existing poems
- deleting poems
- formatting poem text (line cleanup)
- auto-detecting the first line
- enabling/disabling poems for recommendation
- viewing recent audio submissions

## Local run without Docker

### 1. Create virtual environment

```bash
python -m venv venv
```

Linux / macOS:

```bash
source venv/bin/activate
```

Windows CMD:

```cmd
venv\Scripts\activate.bat
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Set at least:

```env
TELEGRAM_BOT_TOKEN=your_telegram_token
BACKEND_PUBLIC_URL=http://localhost:8000
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

For local run (without Docker), `BACKEND_PUBLIC_URL` must stay on `localhost` or `127.0.0.1`.

### 4. Start backend

```bash
python -m uvicorn app.main:app --reload
```

### 5. Start bot in another terminal

```bash
python -m bot.main
```

### 6. Verify backend

- Health: `http://127.0.0.1:8000/health`
- Admin panel: `http://127.0.0.1:8000/admin/`
- Swagger: `http://127.0.0.1:8000/docs`

## Docker run

### 1. Prepare `.env`

```bash
cp .env.example .env
```

In Docker mode, `docker-compose.yml` overrides bot backend URL to `http://backend:8000` automatically.

### 2. Build and run

```bash
docker compose up -d --build
```

### 3. Check logs

```bash
docker compose logs -f backend
docker compose logs -f bot
```

## API endpoints

### Text chat

```bash
POST /api/chat
```

### Audio logging

```bash
POST /api/audio-message
```

The audio endpoint stores Telegram audio metadata in the database and returns a message asking the user to provide the poem lines as text.

## Notes for coursework defense

If the instructor asks why voice is not transcribed automatically, the answer is simple:

> The project intentionally avoids external AI APIs and neural networks. Audio messages are still accepted by the system and recorded in the learner profile, while memorization assessment is performed deterministically on text input.

## MIT License

See `LICENSE`.
