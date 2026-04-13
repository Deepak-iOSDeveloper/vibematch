# VibeMatch Django 🌸

> A dating app for Indian college students — connect through conversation, not appearance.
> Built with Django + Channels (WebSocket) + SQLite/PostgreSQL.

---

## Quick Start (5 minutes)

### Step 1 — Set up virtual environment
```bash
cd vibematch_django
python -m venv venv
source venv/bin/activate          # Mac/Linux
venv\Scripts\activate             # Windows
```

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment
```bash
cp .env.example .env
```
Open `.env` and set a `SECRET_KEY` (any long random string works for local dev — leave others as-is).

### Step 4 — Run migrations
```bash
python manage.py migrate
```

### Step 5 — Seed daily prompts
```bash
python manage.py seed_data
```

### Step 6 — Create admin user (optional)
```bash
python manage.py createsuperuser
```

### Step 7 — Run the server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** — you'll see the VibeMatch landing page.

---

## Features

### Auth & Onboarding
- Email/password signup and login
- 6-step onboarding: Basics → Academic → Personality → Interests → Preferences → Icebreaker
- Avatar color selection (no photo required to start)
- Profile completeness guard — incomplete profiles redirected to onboarding

### Discover
- Browse profiles filtered by region
- Transparent **Vibe Score** broken into Interests / Values / Humor
- Shared interests highlighted on each card
- Photos always locked (reveal requires mutual consent)
- **Daily Question Prompt** — answer it to add to your profile
- Smart conversation starter suggestions based on shared interests

### Real-time Chat (WebSockets via Django Channels)
- Conversation starters inbox — accept or decline
- Real-time messaging — no page refresh needed
- Day counter shown in chat header (Day 1–7)
- Auto-scrolling messages with timestamps

### 7-Day Vibe Check
- Auto-triggered after 7 days of chatting
- Three responses: Explore more / Stay friends / Part ways
- Both users respond independently
- Status resolves to: matched / friends / ended

### Photo Reveal System
- Request sent to the other person
- Photos unlock only when both sides request
- Enforced at the view level

### Safety & Ethics
- Report user with categorized reasons
- Block user — ends any active connection
- Community Guidelines visible in settings
- Admin panel for reviewing reports

### Notifications
- Bell icon with unread count (polls every 30 seconds)
- Types: new starter, new message, vibe check, reveal, match
- Auto-marked as read on open

### Profile & Settings
- Inline editing of bio, icebreaker, interests, personality
- Photo upload (revealed only with mutual consent)
- Account deactivation

---

## Project Structure

```
vibematch_django/
├── accounts/                   # Custom User model, auth, onboarding
│   ├── models.py               # User with 40+ profile fields
│   ├── views.py                # signup, login, onboarding (6 steps), edit profile
│   ├── forms.py                # All form classes
│   └── urls.py
├── core/                       # Main app — discover, chat, connections
│   ├── models.py               # Connection, Message, DailyPrompt, Notification, Report, Block
│   ├── views.py                # All page views + AJAX endpoints
│   ├── consumers.py            # WebSocket ChatConsumer
│   ├── routing.py              # WebSocket URL routing
│   ├── urls.py
│   └── management/commands/
│       └── seed_data.py        # Seeds 30 daily prompts
├── templates/
│   ├── base.html               # Base HTML shell
│   ├── app_base.html           # App shell with top + bottom nav
│   ├── accounts/
│   │   ├── auth.html           # Login / Signup
│   │   ├── onboarding.html     # 6-step onboarding
│   │   └── edit_profile.html
│   └── core/
│       ├── landing.html
│       ├── discover.html
│       ├── chat_list.html
│       ├── chat.html           # Real-time WebSocket chat
│       ├── profile.html
│       ├── notifications.html
│       └── settings.html
├── static/
│   └── css/main.css            # Complete design system
├── vibematch/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py                 # ASGI + Channels config
│   └── wsgi.py
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Deploying to Railway (Recommended — Free Tier)

Railway is the easiest deployment option for Django.

### Step 1
Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo

### Step 2
Add these environment variables in Railway dashboard:

```
SECRET_KEY=your-long-random-secret-key
DEBUG=False
ALLOWED_HOSTS=yourapp.railway.app
DATABASE_URL=<auto-provided by Railway PostgreSQL>
```

### Step 3
Add a PostgreSQL database: New Service → Database → PostgreSQL
Railway auto-sets `DATABASE_URL`.

### Step 4
Add a `Procfile` in your project root:
```
web: daphne -b 0.0.0.0 -p $PORT vibematch.asgi:application
release: python manage.py migrate && python manage.py seed_data
```

### Step 5
Push to GitHub — Railway auto-deploys on every push.

---

## Deploying to PythonAnywhere (Also Free)

1. Upload your project files
2. Create a virtualenv and `pip install -r requirements.txt`
3. Set `DEBUG=False` and your domain in `ALLOWED_HOSTS`
4. Run `python manage.py migrate && python manage.py seed_data`
5. Configure WSGI file to point to `vibematch.wsgi`

Note: PythonAnywhere free tier doesn't support WebSockets — chat will require page refresh. Upgrade to paid tier for real-time messaging.

---

## Admin Panel

Go to `/admin/` and log in with your superuser credentials.

From the admin you can:
- View and ban users
- Review reports
- Add/edit daily prompts
- Monitor connections and messages

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 4.2 |
| Real-time | Django Channels + ASGI |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | Django built-in auth with custom User model |
| Frontend | Django templates + vanilla JS |
| Fonts | DM Serif Display + DM Sans (Google Fonts) |
| Deployment | Railway / PythonAnywhere / Render |

---

Built with 🤍 for meaningful connections among Indian college students.
