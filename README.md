# Gaffer - AI-Powered Meeting Hype Generator

Gaffer connects to your Google Calendar and delivers AI-generated football manager-style motivational speeches before your meetings. Choose your manager, click "Hype Me", and get pumped up with a personalized team talk complete with text-to-speech audio.

Each meeting is automatically scored for importance using AI, so you know which meetings deserve the most hype.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (apps/web)                            │
│                       Vite + React 19 + TanStack                         │
│                                                                          │
│         ┌────────────┐       ┌────────────┐       ┌────────────┐         │
│         │  Events    │       │   Hype     │       │   Audio    │         │
│         │   List     │──────▶│ Generation │──────▶│   Player   │         │
│         └─────┬──────┘       └─────┬──────┘       └────────────┘         │
│               │                    │                                     │
└───────────────┼────────────────────┼─────────────────────────────────────┘
                │                    │
                │  All requests include Supabase JWT
                ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (apps/api)                             │
│                              FastAPI                                     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                      Auth Middleware                            │     │
│  │              Verify JWT via Supabase Auth API ─────────────────────┐  │
│  └─────────────────────────────────────────────────────────────────┘  │  │
│                                                                       │  │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐            │  │
│  │  /calendar/*  │   │ /hype/generate│   │  /hype/audio  │            │  │
│  │               │   │               │   │               │            │  │
│  │ • Sync events │   │ • Claude AI   │   │ • ElevenLabs  │            │  │
│  │ • Cache in DB │   │ • Store in DB │   │ • Store audio │            │  │
│  └───────┬───────┘   └───────┬───────┘   └───┬───────┬───┘            │  │
│          │                   │               │       │                │  │
│          │    ┌──────────────┘               │       │                │  │
│          │    │    ┌─────────────────────────┘       │                │  │
│          ▼    ▼    ▼                                 │                │  │
│  ┌──────────────────────┐  ┌──────────────────────┐  │                │  │
│  │    SQLAlchemy ORM    │  │    Cache Service     │  │                │  │
│  └──────────┬───────────┘  └──────────┬───────────┘  │                │  │
│             │                         │              │                │  │
└─────────────┼─────────────────────────┼──────────────┼────────────────┼──┘
              │                         │              │                │
              ▼                         ▼              ▼                ▼
    ┌─────────────────┐       ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐
    │   PostgreSQL    │       │     Redis       │ │  Supabase   │ │  Supabase   │
    │   (Supabase)    │       │   (Upstash)     │ │   Storage   │ │    Auth     │
    │                 │       │                 │ │             │ │             │
    │  • tokens (enc) │       │ • access tokens │ │ • Audio     │ │ • JWT verify│
    │  • events cache │       │   (~50min TTL)  │ │   files     │ └─────────────┘
    │  • sync state   │       │ • rate limits   │ └─────────────┘
    │  • hype records │       └─────────────────┘
    │  • subscriptions│
    └────────┬────────┘
             │
             │ encrypted Google refresh tokens
             ▼
    ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
    │  Google         │      │   Anthropic     │      │   ElevenLabs    │
    │  Calendar API   │      │   Claude API    │      │   TTS API       │
    │                 │      │                 │      │                 │
    │  • Fetch events │      │  • Generate     │      │  • Text to      │
    │                 │      │    hype text    │      │    speech       │
    └─────────────────┘      └─────────────────┘      └─────────────────┘
             ▲                       ▲                        ▲
             │                       │                        │
             └───── OAuth tokens ────┴──── API keys ──────────┘
                    from DB                from env
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
- **Database**: SQLAlchemy 2.0 (async) with asyncpg
- **Caching**: Redis (Upstash) with in-memory fallback
- **Auth Validation**: Supabase Auth (JWT verification)
- **File Storage**: Supabase Storage (audio files)
- **Migrations**: Alembic
- **Token Encryption**: Cryptography (Fernet)
- **Testing**: pytest with testcontainers (PostgreSQL)

### Infrastructure
- **Database**: Supabase (PostgreSQL with PgBouncer)
- **Cache**: Upstash Redis (Fly.io native integration)
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage
- **Package Manager**: pnpm (monorepo)
- **Frontend Hosting**: Cloudflare Pages
- **Backend Hosting**: Fly.io
- **CI**: GitHub Actions

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
│   │   │   │   ├── privacy.tsx       # Privacy policy
│   │   │   │   ├── terms.tsx         # Terms of service
│   │   │   │   └── (protected)/      # Auth-protected routes
│   │   │   │       ├── route.tsx     # Protected layout
│   │   │   │       └── dashboard.tsx # Main app
│   │   │   ├── components/
│   │   │   │   ├── ui/               # Reusable UI components
│   │   │   │   │   └── audio-player/ # Audio playback system
│   │   │   │   ├── event-card.tsx
│   │   │   │   ├── events-list.tsx
│   │   │   │   ├── importance-badge.tsx
│   │   │   │   ├── manager-selector.tsx
│   │   │   │   ├── google-reconnect-banner.tsx
│   │   │   │   ├── error-boundary.tsx
│   │   │   │   └── landing/          # Landing page sections
│   │   │   ├── hooks/
│   │   │   │   ├── use-calendar-events.ts
│   │   │   │   ├── use-hype-generation.ts
│   │   │   │   ├── use-hype-history.ts
│   │   │   │   ├── use-usage.ts
│   │   │   │   └── use-upgrade-interest.ts
│   │   │   └── lib/
│   │   │       ├── supabase.ts
│   │   │       ├── supabase-provider.tsx
│   │   │       ├── theme-provider.tsx
│   │   │       └── utils.ts
│   │   └── package.json
│   │
│   └── api/                          # Backend
│       ├── app/
│       │   ├── main.py               # FastAPI app entry
│       │   ├── config.py             # Pydantic settings
│       │   ├── types.py              # Shared Literal types (ManagerStyle, HypeStatus, etc.)
│       │   ├── rate_limiter.py       # Rate limiting config
│       │   ├── routers/
│       │   │   ├── hype.py           # /hype endpoints
│       │   │   ├── calendar.py       # /calendar endpoints
│       │   │   └── auth.py           # /auth endpoints
│       │   ├── services/
│       │   │   ├── hype_generator.py        # Claude integration
│       │   │   ├── hype_storage_service.py  # Hype persistence + audio storage
│       │   │   ├── calendar_sync_service.py # Calendar sync & caching
│       │   │   ├── google_token_service.py  # Token encryption & refresh
│       │   │   ├── meeting_scorer_service.py # AI-based meeting importance scoring
│       │   │   ├── usage_service.py         # Usage tracking & monthly limits
│       │   │   ├── upgrade_interest_service.py # Upgrade interest registration
│       │   │   ├── cache_service.py         # Redis with in-memory fallback
│       │   │   ├── database.py              # SQLAlchemy async engine
│       │   │   └── supabase_client.py       # Supabase Auth & Storage
│       │   ├── models/               # SQLAlchemy models
│       │   │   ├── base.py
│       │   │   ├── user_google_token.py
│       │   │   ├── calendar_event.py
│       │   │   ├── calendar_sync_state.py
│       │   │   ├── hype_record.py
│       │   │   ├── user_subscription.py
│       │   │   └── upgrade_interest.py
│       │   └── prompts/
│       │       └── manager_styles.py # Manager personalities
│       ├── migrations/               # Alembic migrations
│       │   ├── env.py
│       │   └── versions/
│       ├── tests/                    # Test suite
│       │   ├── conftest.py           # Shared fixtures
│       │   ├── unit/
│       │   │   └── services/         # Service unit tests
│       │   └── integration/
│       │       └── routers/          # Integration tests (PostgreSQL via Docker)
│       ├── alembic.ini
│       ├── pyproject.toml            # mypy, ruff, pytest config
│       ├── requirements.txt
│       └── requirements-dev.txt      # Test dependencies
│
├── .github/workflows/ci.yml         # CI pipeline
├── package.json                      # Workspace root
├── pnpm-workspace.yaml
└── README.md
```

## API Documentation

Interactive API docs available at: **http://localhost:8000/docs**

## Setup

### Prerequisites
- Node.js 20+
- Python 3.12+
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
# Use the "Transaction" pooler connection string for PgBouncer compatibility
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres

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

# Redis (optional - falls back to in-memory cache if not set)
REDIS_URL=redis://default:password@your-redis-host:6379
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
alembic upgrade head
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

## Deployment

### Frontend (Cloudflare Pages)

The frontend is deployed via Cloudflare Pages with GitHub integration:

1. Connect your GitHub repo in Cloudflare Pages dashboard
2. Set build command: `pnpm --filter @gaffer/web build`
3. Set build output directory: `apps/web/dist`
4. Set root directory: `/`
5. Add environment variables in Cloudflare dashboard:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_URL` (your Fly.io backend URL)

### Backend (Fly.io)

The backend is deployed via Fly.io with GitHub integration:

1. Install flyctl and authenticate: `fly auth login`
2. Create app from `apps/api`: `fly launch`
3. Set secrets:
   ```bash
   fly secrets set DATABASE_URL=... \
     SUPABASE_URL=... \
     SUPABASE_SERVICE_ROLE_KEY=... \
     GOOGLE_CLIENT_ID=... \
     GOOGLE_CLIENT_SECRET=... \
     TOKEN_ENCRYPTION_KEY=... \
     ANTHROPIC_API_KEY=... \
     ELEVENLABS_API_KEY=... \
     REDIS_URL=... \
     FRONTEND_URL=https://your-app.pages.dev
   ```
4. Connect GitHub for auto-deploy in Fly.io dashboard

### Production OAuth Setup

Update redirect URIs for production:
1. **Supabase**: Authentication → URL Configuration → Add production URL to redirect URLs
2. **Google Cloud Console**: Add production callback URL to authorized redirect URIs

### CI/CD

GitHub Actions runs on every push and PR:

**Frontend:**
- TypeScript type checking
- ESLint linting
- Build verification

**Backend:**
- Unit tests (pytest, SQLite)
- Integration tests (pytest, PostgreSQL via testcontainers)
- Coverage reporting

Deployments are handled by native GitHub integrations:
- Cloudflare Pages auto-deploys on push to main
- Fly.io auto-deploys on push to main

## Database Commands

```bash
cd apps/api

# Apply pending migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Auto-generate migration from model changes
alembic revision --autogenerate -m "description"

# Show current migration version
alembic current
```

## Testing

The backend has a comprehensive test suite covering services and business logic.

### Test Architecture

**Unit tests** run fast without external dependencies and cover:
- Token encryption/decryption
- Cache service with fallback behavior
- Hype text generation and audio tag sanitization
- Meeting importance scoring logic
- Usage tracking and limits
- Cache hit scenarios

**Integration tests** use real PostgreSQL via Docker and cover:
- Database operations (store/retrieve tokens, subscriptions)
- Usage tracking and monthly limits
- Token refresh flows

### Running Tests

```bash
cd apps/api

# Activate virtual environment
source .venv/bin/activate

# Install dev dependencies (first time only)
pip install -r requirements-dev.txt

# Run unit tests only (fast, no Docker needed)
pytest

# Run integration tests (requires Docker)
pytest -m integration

# Run all tests
pytest -m ""

# Run with coverage report
pytest --cov=app --cov-report=html
```

### Test Dependencies

Dev dependencies in `requirements-dev.txt`:
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **pytest-cov** - Coverage reporting
- **testcontainers** - PostgreSQL Docker containers for integration tests
- **respx** - HTTP request mocking
- **freezegun** - Time mocking for date-dependent tests
- **aiosqlite** - SQLite async driver for unit tests

### CI/CD Test Pipeline

GitHub Actions runs tests automatically on every push and PR:

1. **Unit tests** - Fast feedback, no external services
2. **Integration tests** - Full database tests with testcontainers

Both test suites must pass before deployment.

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
10. Access tokens cached in Redis (~50 min TTL)
11. If refresh token revoked, user sees "Reconnect Google" banner
```

## Security

- **Tokens encrypted at rest**: Google refresh tokens stored with Fernet encryption
- **BFF pattern**: Frontend never handles Google tokens after initial OAuth
- **Short-lived access tokens**: Cached in Redis for 50 minutes, auto-refreshed
- **RLS enabled**: Database row-level security on all tables
- **SQLAlchemy direct access**: Backend uses SQLAlchemy with service-level DB access
- **Supabase Auth**: JWT verification for all API endpoints
- **Supabase Storage**: Audio files stored securely with user-scoped paths
- **Rate limiting**: API endpoints protected with slowapi (10/minute for hype generation)
- **Security headers**: HSTS, X-Content-Type-Options, X-Frame-Options
- **Input validation**: Pydantic validation with length limits on all inputs
- **CSP**: Content Security Policy headers on frontend

## Caching

The backend uses a two-tier caching strategy:

1. **Primary**: Redis (Upstash on Fly.io) for production
2. **Fallback**: In-memory cache if Redis is unavailable

Cached data:
- Google access tokens (~50 min TTL)
- Rate limiting counters

The cache service automatically falls back to in-memory storage if Redis connection fails, ensuring the application remains functional.

## License

MIT
