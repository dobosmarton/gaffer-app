# Gaffer - AI-Powered Meeting Hype Generator

Gaffer connects to your Google Calendar and delivers AI-generated football manager-style motivational speeches before your meetings. Choose your manager, click "Hype Me", and get pumped up with a personalized team talk complete with text-to-speech audio.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (apps/web)                         │
│                      Vite + React 19 + TanStack                      │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Dashboard  │  │   Events    │  │  Manager    │  │    Hype     │ │
│  │    Page     │  │    List     │  │  Selector   │  │   Player    │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘  └──────┬──────┘ │
│         │                │                                  │        │
└─────────┼────────────────┼──────────────────────────────────┼────────┘
          │                │                                  │
          │  Supabase JWT  │  GET /calendar/events            │
          │  (no Google    │  POST /hype/generate             │  POST /hype/audio
          │   tokens!)     │                                  │
          ▼                ▼                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BACKEND (apps/api)                          │
│                             FastAPI                                  │
│                                                                      │
│  ┌───────────────┐  ┌───────────────────┐  ┌───────────────────┐    │
│  │ /calendar/    │  │   /hype/generate  │  │    /hype/audio    │    │
│  │   events      │  │   Claude AI Text  │  │  ElevenLabs TTS   │    │
│  │               │  │     Generation    │  │    Streaming      │    │
│  └───────┬───────┘  └─────────┬─────────┘  └─────────┬─────────┘    │
│          │                    │                      │               │
│          ▼                    │                      │               │
│  ┌───────────────┐            │                      │               │
│  │ Google Token  │            │                      │               │
│  │   Service     │◄───────────┼──────────────────────┘               │
│  │ (encrypted)   │            │                                      │
│  └───────┬───────┘            │                                      │
│          │                    │                                      │
└──────────┼────────────────────┼──────────────────────────────────────┘
           │                    │
           ▼                    ▼
    ┌─────────────┐      ┌─────────────┐       ┌─────────────┐
    │   Google    │      │  Anthropic  │       │  ElevenLabs │
    │  Calendar   │      │  Claude API │       │     API     │
    │     API     │      └─────────────┘       └─────────────┘
    └─────────────┘
           ▲
           │
    ┌─────────────┐
    │  PostgreSQL │
    │  (Supabase) │
    │  encrypted  │
    │   tokens    │
    └─────────────┘
```

**Key Security Features (BFF Pattern):**
- Google refresh tokens are stored **encrypted** in the database (Fernet encryption)
- Frontend **never** handles Google tokens after the initial OAuth callback
- Backend automatically refreshes access tokens when needed
- All Google API calls happen server-side

## Tech Stack

### Frontend (`apps/web`)
- **Framework**: React 19 with Vite
- **Routing**: TanStack Router (file-based)
- **Data Fetching**: TanStack Query
- **Styling**: Tailwind CSS 4
- **Auth**: Supabase Auth (Google OAuth)
- **UI Components**: Radix UI, Lucide Icons, Motion (Framer Motion)

### Backend (`apps/api`)
- **Framework**: FastAPI
- **AI Text Generation**: Anthropic Claude (claude-sonnet-4-20250514)
- **Text-to-Speech**: ElevenLabs SDK (streaming)
- **Auth Validation**: Supabase (JWT verification)
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Token Encryption**: Cryptography (Fernet)

### Infrastructure
- **Auth & Database**: Supabase (PostgreSQL)
- **Package Manager**: pnpm (monorepo)

## Project Structure

```
gaffer/
├── apps/
│   ├── web/                          # Frontend
│   │   ├── src/
│   │   │   ├── routes/               # TanStack Router pages
│   │   │   │   ├── __root.tsx        # Root layout
│   │   │   │   ├── index.tsx         # Landing page
│   │   │   │   ├── login.tsx         # Google OAuth login
│   │   │   │   └── (protected)/      # Auth-protected routes
│   │   │   │       ├── route.tsx     # Protected layout
│   │   │   │       └── dashboard.tsx # Main app
│   │   │   ├── components/
│   │   │   │   ├── ui/               # Reusable UI components
│   │   │   │   │   ├── audio-player.tsx
│   │   │   │   │   ├── bar-visualizer.tsx
│   │   │   │   │   └── shimmering-text.tsx
│   │   │   │   ├── event-card.tsx
│   │   │   │   ├── hype-player.tsx
│   │   │   │   └── manager-selector.tsx
│   │   │   ├── hooks/
│   │   │   │   └── use-calendar-events.ts
│   │   │   └── lib/
│   │   │       ├── supabase.ts
│   │   │       └── supabase-provider.tsx
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── api/                          # Backend
│       ├── app/
│       │   ├── main.py               # FastAPI app entry
│       │   ├── config.py             # Pydantic settings
│       │   ├── routers/
│       │   │   ├── hype.py           # /hype endpoints
│       │   │   ├── calendar.py       # /calendar endpoints
│       │   │   └── auth.py           # /auth endpoints (token storage)
│       │   ├── services/
│       │   │   ├── hype_generator.py # Claude integration
│       │   │   ├── google_token_service.py  # Token encryption & refresh
│       │   │   ├── database.py       # SQLAlchemy async engine
│       │   │   └── supabase_client.py
│       │   ├── models/               # SQLAlchemy models
│       │   │   ├── base.py
│       │   │   └── user_google_token.py
│       │   └── prompts/
│       │       └── manager_styles.py # Manager personalities
│       ├── migrations/               # Alembic migrations
│       │   ├── env.py
│       │   └── versions/
│       ├── alembic.ini
│       ├── requirements.txt
│       └── .env
│
├── package.json                      # Workspace root
├── pnpm-workspace.yaml
└── README.md
```

## API Endpoints

### Backend (`http://localhost:8000`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/store-google-token` | POST | Store encrypted Google refresh token |
| `/auth/google-token-status` | GET | Check if user has stored token |
| `/auth/google-token` | DELETE | Revoke stored tokens |
| `/calendar/events` | GET | Fetch calendar events (uses stored tokens) |
| `/hype/generate` | POST | Generate motivational text using Claude |
| `/hype/audio` | POST | Stream TTS audio from ElevenLabs |

#### POST `/auth/store-google-token`
```
Headers:
  Authorization: Bearer <supabase_jwt>

Body:
{
  "refresh_token": "<google_refresh_token>"
}

Response:
{
  "success": true,
  "message": "Token stored successfully"
}
```

#### GET `/calendar/events`
```
Headers:
  Authorization: Bearer <supabase_jwt>

Query Parameters:
  time_min: ISO datetime (optional, defaults to now)
  time_max: ISO datetime (optional, defaults to +24h)
  max_results: number (optional, defaults to 10)

Response:
{
  "events": [
    {
      "id": "event_id",
      "title": "Q3 Budget Review",
      "description": "Monthly budget review",
      "start": "2024-01-15T14:00:00Z",
      "end": "2024-01-15T15:00:00Z",
      "location": "Conference Room A",
      "attendees": 5
    }
  ]
}
```

#### POST `/hype/generate`
```json
// Request
{
  "event_title": "Q3 Budget Review",
  "event_description": "Monthly budget review with finance team",
  "event_time": "2024-01-15T14:00:00Z",
  "manager_style": "ferguson"  // ferguson | mourinho | klopp | guardiola | bielsa
}

// Response
{
  "hype_id": "uuid",
  "hype_text": "RIGHT, LISTEN UP...",
  "manager": "ferguson",
  "status": "text_ready"
}
```

#### POST `/hype/audio`
```json
// Request
{
  "text": "RIGHT, LISTEN UP...",
  "voice_id": "optional_voice_id"
}

// Response: audio/mpeg stream
```

## Setup

### Prerequisites
- Node.js 20+
- Python 3.11+
- pnpm
- Supabase account
- Google Cloud Console project (for OAuth)
- Anthropic API key
- ElevenLabs API key

### 1. Clone and Install

```bash
# Install dependencies
pnpm install

# Set up Python virtual environment
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables

#### Frontend (`apps/web/.env`)
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000
```

#### Backend (`apps/api/.env`)
```env
APP_ENV=development
FRONTEND_URL=http://localhost:3000

# Database (get from Supabase Dashboard → Settings → Database → Connection string)
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Google OAuth (for server-side token refresh)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret

# Token encryption key (generate with command below)
TOKEN_ENCRYPTION_KEY=your-fernet-key

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=wo6udizrrtpIxWGp2qJk
```

Generate a Fernet encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Configure Supabase Auth

1. Go to Supabase Dashboard → Authentication → Providers → Google
2. Enable Google provider
3. Add your Google OAuth credentials
4. Add `https://www.googleapis.com/auth/calendar.readonly` to the scopes

### 4. Configure Google Cloud Console

1. Create OAuth 2.0 credentials
2. Add authorized redirect URI: `https://your-project.supabase.co/auth/v1/callback`
3. Enable Google Calendar API
4. Copy Client ID and Client Secret to backend `.env`

### 5. Run Database Migrations

```bash
cd apps/api
pnpm run db:migrate
```

### 6. Run the Apps

```bash
# Terminal 1: Frontend
cd apps/web
pnpm dev

# Terminal 2: Backend
cd apps/api
pnpm run dev
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Database Commands

```bash
cd apps/api

# Apply pending migrations
pnpm run db:migrate

# Rollback last migration
pnpm run db:rollback

# Auto-generate migration from model changes
pnpm run db:generate "description"

# Show current migration version
pnpm run db:status
```

## Manager Personalities

| Manager | Style |
|---------|-------|
| **Sir Alex Ferguson** | Intense, demanding, legendary Manchester United manager |
| **Jose Mourinho** | Confident, psychological, "The Special One" |
| **Jurgen Klopp** | Enthusiastic, emotional, heavy metal football |
| **Pep Guardiola** | Tactical, cerebral, control-focused |
| **Marcelo Bielsa** | Philosophical, dignified, principled |

## Authentication Flow

```
1. User clicks "Sign in with Google"
2. Supabase redirects to Google OAuth with calendar.readonly scope
3. User grants permission, Google redirects back with tokens
4. Supabase session includes provider_refresh_token (one-time)
5. Frontend immediately sends refresh token to backend /auth/store-google-token
6. Backend encrypts token and stores in user_google_tokens table
7. Frontend discards Google tokens - only keeps Supabase JWT
8. All subsequent API calls use Supabase JWT for auth
9. Backend retrieves encrypted refresh token, exchanges for access token
10. Access tokens cached in memory (~50 min TTL)
11. If refresh token revoked, user sees "Reconnect Google" banner
```

## Security

- **Tokens encrypted at rest**: Google refresh tokens stored with Fernet encryption
- **BFF pattern**: Frontend never handles Google tokens after initial OAuth
- **Short-lived access tokens**: Cached for 50 minutes, auto-refreshed
- **RLS enabled**: Database row-level security on token table
- **Service role key**: Backend uses Supabase service role for DB access

## License

MIT
