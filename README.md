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
          │  GET /calendar/events      POST /hype/generate    │  POST /hype/audio
          │  X-Google-Token header     { event_title, ... }   │  { text }
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
└──────────┼────────────────────┼──────────────────────┼───────────────┘
           │                    │                      │
           ▼                    ▼                      ▼
    ┌─────────────┐      ┌─────────────┐       ┌─────────────┐
    │   Google    │      │  Anthropic  │       │  ElevenLabs │
    │  Calendar   │      │  Claude API │       │     API     │
    │     API     │      └─────────────┘       └─────────────┘
    └─────────────┘
```

**Key Points:**
- **All external APIs** are called through the backend for consistency and security
- Frontend passes the Google OAuth token to backend via `X-Google-Token` header
- Google token is short-lived (~1 hour) - users see a "Reconnect" banner after expiry

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

### Infrastructure
- **Auth & Database**: Supabase
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
│       │   │   └── auth.py           # /auth endpoints
│       │   ├── services/
│       │   │   ├── hype_generator.py # Claude integration
│       │   │   └── supabase_client.py
│       │   └── prompts/
│       │       └── manager_styles.py # Manager personalities
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
| `/calendar/events` | GET | Fetch calendar events from Google Calendar |
| `/hype/generate` | POST | Generate motivational text using Claude |
| `/hype/audio` | POST | Stream TTS audio from ElevenLabs |

#### GET `/calendar/events`
```
Headers:
  X-Google-Token: <google_access_token>

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

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
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

### 5. Run the Apps

```bash
# Terminal 1: Frontend
cd apps/web
pnpm dev

# Terminal 2: Backend
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Manager Personalities

| Manager | Style |
|---------|-------|
| **Sir Alex Ferguson** | Intense, demanding, legendary Manchester United manager |
| **Jose Mourinho** | Confident, psychological, "The Special One" |
| **Jurgen Klopp** | Enthusiastic, emotional, heavy metal football |
| **Pep Guardiola** | Tactical, cerebral, control-focused |
| **Marcelo Bielsa** | Philosophical, dignified, principled |

## Flow

1. User logs in with Google via Supabase Auth (grants calendar read access)
2. Frontend receives Google OAuth token from Supabase session
3. Frontend calls backend `/calendar/events` with token in `X-Google-Token` header
4. Backend fetches events from Google Calendar API and returns them
5. Dashboard displays upcoming events
6. User selects a manager personality
7. User clicks "Hype Me" on an event
8. Frontend calls backend `/hype/generate` → Claude generates motivational text
9. Text is displayed immediately while audio generates
10. Frontend calls backend `/hype/audio` → ElevenLabs streams TTS audio
11. User listens to their personalized team talk

**Note:** Google token is only available immediately after OAuth login (~1 hour lifetime). If the page is refreshed or token expires, user sees a "Reconnect Google" banner to re-authenticate.

## License

MIT
