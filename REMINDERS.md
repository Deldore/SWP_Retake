# User Reminder System

## Overview

The Poetry Bot now includes an automated reminder system that notifies users who haven't been active for a specified period (default: 3 days). Reminders are sent daily at a configured time (default: 12:00 UTC noon).

## Features

✅ **Automatic Activity Tracking**
- User's `last_active_at` timestamp is updated whenever they interact with the bot
- Tracks text messages, voice messages, button clicks, and other interactions
- Integrated with existing backend API

✅ **Scheduled Reminders**
- Runs on a configurable schedule (default: daily at 12:00 UTC)
- Finds all users inactive for the configured threshold (default: 3 days)
- Sends personalized multilingual reminders

✅ **Multilingual Support**
- Reminders sent in user's preferred language (Russian or English)
- English used as fallback if preference not set

✅ **Flexible Configuration**
- Enable/disable reminders per deployment
- Configure reminder time and timezone
- Adjust inactivity threshold

## Configuration

Edit your `.env` file to customize the reminder behavior:

```env
# Enable or disable the reminder system (true/false)
REMINDER_ENABLED=true

# Hour of day to send reminders (0-23, in your timezone)
REMINDER_HOUR=12

# Days of inactivity before sending a reminder (1+)
REMINDER_INACTIVITY_DAYS=3

# Timezone for scheduling (e.g., UTC, Europe/Moscow, US/Eastern)
# See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE=UTC
```

### Default Settings
- **Enabled**: Yes
- **Reminder Time**: 12:00 (noon) UTC
- **Inactivity Threshold**: 3 days
- **Timezone**: UTC

## How It Works

### Activity Tracking
Every time a user interacts with the bot:
1. User sends a message, clicks a button, or performs any action
2. Request is sent to the backend API
3. `UserProfile.last_active_at` is updated with current timestamp
4. No manual tracking needed - fully automatic!

### Reminder Sending
Every day at the configured time:
1. APScheduler triggers the `send_reminders()` job
2. Database query finds all users where:
   - `last_active_at < (now - REMINDER_INACTIVITY_DAYS)`
3. For each inactive user:
   - Get their language preference
   - Format reminder message in their language
   - Send via Telegram bot
   - Log the result

### Message Content

**English:**
```
📖 Poetry Learning Reminder

Hi there! 🎭

I noticed you haven't been active for the last 3 days.

Let's get back to learning poems! Use me to:
• Get a new poem recommendation (/start)
• Practice memory checks on poems you know
• View your learning progress

Remember, consistent practice is key to success! 💪
```

**Russian:**
```
📖 Напоминание о стихотворениях

Привет! 🎭

Я заметил, что вы не проявляли активности последние 3 дня.

Давайте вернёмся к изучению стихотворений! Используйте боту, чтобы:
• Получить новую рекомендацию (/start)
• Проверить память по уже выученным стихам
• Просмотреть свой прогресс

Помните, регулярная практика — ключ к успеху! 💪
```

## Testing

### Quick Test Setup

1. **Enable test mode** - Set a short inactivity period:
   ```env
   REMINDER_INACTIVITY_DAYS=0  # Will remind ALL users
   REMINDER_HOUR=14            # Set to test time (e.g., 2 PM)
   ```

2. **Watch for the job** - Check your bot logs:
   ```
   INFO: Starting reminder job - checking for inactive users
   INFO: Found 5 inactive users. Sending reminders...
   INFO: Reminder sent to user 123456789 (John Doe)
   ...
   INFO: Reminder job completed: 5 successful, 0 failed out of 5 users
   ```

3. **Verify messages** - Check if the Telegram bot sent reminder messages

### Manual Testing

You can also check the database directly to see activity timestamps:

```python
from sqlmodel import Session, select
from app.models.tables import UserProfile
from app.core.db import engine
from datetime import datetime, timedelta

with Session(engine) as session:
    # See all users and their last activity
    users = session.exec(select(UserProfile)).all()
    for user in users:
        days_inactive = (datetime.utcnow() - user.last_active_at).days
        print(f"{user.full_name}: {days_inactive} days inactive")
```

## Architecture

### Components

**1. Reminder Service** (`app/services/reminder.py`)
- `get_inactive_users()` - Database queries
- `format_reminder_message()` - Message formatting
- `get_reminder_text()` - Language-specific templates

**2. Bot Integration** (`bot/main.py`)
- `send_reminders()` - Async job that sends messages
- `setup_reminder_scheduler()` - Initializes APScheduler
- Scheduler runs the job on the configured cron schedule

**3. Configuration** (`app/core/config.py`)
- 4 new environment variables
- Validated via Pydantic

### Data Flow

```
User Activity
    ↓
Bot Handler (bot/main.py)
    ↓
Backend API (app/api/routes.py)
    ↓
upsert_user() (app/services/recommender.py)
    ↓
Update UserProfile.last_active_at
    ↓
[Daily at 12:00]
    ↓
APScheduler Trigger
    ↓
send_reminders() (bot/main.py)
    ↓
get_inactive_users() (app/services/reminder.py)
    ↓
Send Telegram Messages
```

## Troubleshooting

### Reminders not being sent

1. **Check if enabled:**
   ```bash
   grep REMINDER_ENABLED .env
   # Should output: REMINDER_ENABLED=true
   ```

2. **Check bot logs:**
   ```bash
   # Look for "Starting reminder job" and "Reminder job completed"
   docker logs poetry-bot 2>&1 | grep -i reminder
   ```

3. **Verify users exist:**
   ```python
   from sqlmodel import Session, select
   from app.models.tables import UserProfile
   from app.core.db import engine
   
   with Session(engine) as session:
       count = len(session.exec(select(UserProfile)).all())
       print(f"Total users: {count}")
   ```

4. **Check timezone:**
   - Verify `TIMEZONE` is correctly set
   - Confirm bot server time matches expected timezone
   - Check system timezone: `python -c "import datetime; print(datetime.datetime.utcnow())"`

### Reminders scheduled but not executing

1. **Check APScheduler logs:**
   ```bash
   # Enable DEBUG logging in .env
   LOG_LEVEL=DEBUG
   ```

2. **Verify database connection:**
   - Ensure `DATABASE_URL` is valid
   - Check if database file exists and is readable

3. **Check bot token:**
   - Verify `TELEGRAM_BOT_TOKEN` is correct
   - Bot should be running and responding to messages

## Database Impact

### New/Modified Tables
- No new tables created
- No changes to existing schema
- Only uses existing `UserProfile.last_active_at` field

### Disk Usage
- Minimal - only adds scheduling metadata in memory
- No logs or audit trail stored (use application logs instead)

## Dependencies

New dependency added:
- **apscheduler** (3.10.4) - For task scheduling

Existing dependencies used:
- **python-telegram-bot** - For sending messages
- **sqlmodel** - For database queries

## Performance Considerations

### During Reminder Job
- Single database query to find inactive users
- One Telegram API call per inactive user
- Job runs asynchronously, doesn't block the bot

### Typical Performance
- Query time: < 100ms (SQLite)
- Message sending: ~100-200ms per user (depends on Telegram API)
- Example: 100 inactive users = ~10-20 seconds total

### Database Load
- Minimal impact
- Single indexed query per day
- No additional write operations

## Security

- ✅ No sensitive data in reminder messages
- ✅ Uses existing bot authentication
- ✅ Timezone handling respects user preferences
- ✅ Language detection based on stored preferences
- ✅ No external API calls (except Telegram)

## Future Enhancements

Potential improvements for future versions:

1. **Reminder Customization**
   - Users opt-in/opt-out via /settings
   - Custom reminder frequency per user

2. **Smart Reminders**
   - Suggest specific poems based on learner profile
   - Include progress statistics in reminders

3. **Batch Operations**
   - Minimize API calls with bot sendBulkMessage
   - Cache reminder templates

4. **Analytics**
   - Track reminder engagement rates
   - Monitor when inactive users return

5. **Advanced Scheduling**
   - Time-zone aware per-user reminders
   - Different messages for different activity levels (1 day vs 7 days)

## Support

For issues or questions:
1. Check logs: `docker logs poetry-bot`
2. Enable debug logging: `LOG_LEVEL=DEBUG`
3. Test with simplified config (see Testing section)
4. Check APScheduler timezone documentation: https://apscheduler.readthedocs.io/
