<div align="center">

# DriveEase

**A full-stack car rental booking management system.**

Browse a vehicle catalog, book cars with risk-based dynamic pricing, manage the fleet across customer / employee / technician / admin roles, and leave reviews — all backed by PostgreSQL, MongoDB, and Redis.

![Next.js](https://img.shields.io/badge/Next.js-16-black?logo=next.js)
![React](https://img.shields.io/badge/React-19-blue?logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

</div>

---

## Overview

DriveEase pairs a **Next.js** frontend with an async **FastAPI** backend and a polyglot persistence layer. It models a realistic rental domain — vehicles and categories, reservations and rentals, users with distinct roles, dynamic pricing driven by accident-risk classification, service orders, and a moderated review system.

The full stack runs with a single `docker compose up`, fronted by an nginx reverse proxy.

## Features

- **Authentication** — registration, login, email verification, and password reset using JWT stored in `httpOnly` cookies.
- **Vehicle catalog** — browsable, filterable list of vehicles with image galleries, availability calendars, and detail panels.
- **Role-based access** — `customer`, `employee`, `technician`, and `admin` roles with dedicated dashboard panels.
- **Dynamic pricing** — `base_price × category_multiplier × days`, then adjusted by a per-user risk multiplier, exposed via a price-breakdown endpoint.
- **Risk-based classification** — a per-user `risk_score` (0–100) derived from rental history and incidents, applied at quote time.
- **Reservations & rentals** — book vehicles, then handle pickup and return workflows.
- **Service orders** — technicians track vehicle maintenance and service history.
- **Review system** — star ratings and reviews per vehicle, with admin moderation and aggregate scores.
- **Dark / light theme** and groundwork for i18n.

## Architecture

```
                  ┌─────────────┐
   Browser  ──▶   │    nginx    │   :80   (reverse proxy)
                  └──────┬──────┘
              /          │          /api/, /docs, /static
       ┌──────▼──────┐   │   ┌──────▼──────┐
       │  frontend   │   │   │   backend   │
       │  Next.js    │   │   │  FastAPI    │
       │   :3000     │   │   │   :8000     │
       └─────────────┘   │   └──────┬──────┘
                         │          │
                  ┌──────┴───┬──────┴─────┐
                  ▼          ▼            ▼
            ┌───────────┐ ┌────────┐ ┌────────┐
            │PostgreSQL │ │MongoDB │ │ Redis  │
            │  :5432    │ │ :27017 │ │ :6379  │
            └───────────┘ └────────┘ └────────┘
```

| Store | Role |
| --- | --- |
| **PostgreSQL** | Core relational data — users, vehicles, categories, reservations, rentals, reviews, service orders. |
| **MongoDB** | Document data — rental logs/analytics, incidents/accidents, UI preferences. |
| **Redis** | Sessions, user cache, vehicle-availability cache, rate limiting. |

nginx terminates all traffic on port 80: `/` proxies to the Next.js app, while `/api/`, `/docs`, `/redoc`, and `/static/` proxy to FastAPI (which runs with `root_path="/api"`).

## Tech Stack

**Frontend** — Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Radix UI / shadcn, SWR, lucide-react.

**Backend** — FastAPI, SQLAlchemy 2 (async, asyncpg), Alembic, Pydantic v2, Motor (MongoDB), redis-py, python-jose (JWT), passlib/bcrypt.

**Infrastructure** — Docker Compose, nginx, PostgreSQL 17, MongoDB 7, Redis 7, pgAdmin, Mailpit (dev SMTP).

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) with Docker Compose
- For local (non-Docker) development: [Node.js](https://nodejs.org/) 20+ and [Python](https://www.python.org/) 3.12+

### Quick start (Docker)

```bash
git clone https://github.com/kl0cek/car-rental-system.git
cd car-rental-system
cp .env.example .env          # then set a real SECRET_KEY
docker compose up --build
```

Once the stack is healthy:

| Service | URL | Credentials |
| --- | --- | --- |
| App (via nginx) | http://localhost | — |
| API docs (Swagger) | http://localhost/docs | — |
| pgAdmin | http://localhost:5050 | `admin@driveease.com` / `admin` |
| Mailpit (dev inbox) | http://localhost:8025 | — |

> [!TIP]
> Run `docker compose up -d` to start in the background, then `docker compose logs -f backend` to follow backend logs.

## Local Development

Run the apps natively for hot reload. You'll still need PostgreSQL, MongoDB, and Redis available — the easiest path is to start just those with `docker compose up postgres mongo redis`.

### Backend (`car-rental-backend/`)

```bash
cd car-rental-backend
python -m venv venv
source venv/Scripts/activate          # Windows (Git Bash); use venv/bin/activate on macOS/Linux
pip install -r requirements.txt
alembic upgrade head                  # apply database migrations
uvicorn app.main:app --reload         # dev server on :8000
```

> [!NOTE]
> On Windows the `fastapi dev` CLI has a Unicode rendering issue under the cp1250 code page — use `uvicorn` directly as shown above.

### Frontend (`car-rental-frontend/`)

```bash
cd car-rental-frontend
npm install
npm run dev        # dev server on :3000
```

Other frontend scripts: `npm run build`, `npm run start`, `npm run lint`, `npm run type-check`, `npm run format`.

## Configuration

Backend settings are read from `.env` / environment variables (see `.env.example` and `app/config.py`):

| Variable | Description | Example |
| --- | --- | --- |
| `SECRET_KEY` | JWT signing key — **change in production**. | `change-me-in-production` |
| `DATABASE_URL` | Async PostgreSQL connection string. | `postgresql+asyncpg://postgres:postgres@localhost:5432/driveease` |
| `MONGODB_URL` | MongoDB connection string. | `mongodb://localhost:27017/driveease` |
| `REDIS_URL` | Redis connection string. | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed origins (JSON array). | `["http://localhost:3000"]` |
| `SMTP_HOST` / `SMTP_PORT` | Outbound email (Mailpit in dev). | `mailpit` / `1025` |

> [!WARNING]
> The default credentials and `SECRET_KEY` are for local development only. Always override them before deploying.

## API

The backend exposes a REST API served under nginx's `/api` prefix. Explore it interactively at `/docs` (Swagger UI) or `/redoc`.

| Resource | Path | Purpose |
| --- | --- | --- |
| Auth | `/api/auth` | Register, login, verify email, reset password (JWT cookies). |
| Categories | `/api/categories` | Vehicle categories & price multipliers. |
| Vehicles | `/api/vehicles` | Catalog, details, availability, images. |
| Reservations | `/api/reservations` | Create and manage bookings. |
| Rentals | `/api/rentals` | Pickup and return workflows. |
| Pricing | `/api/pricing` | Dynamic price breakdown. |
| Reviews | `/api/reviews` | Vehicle reviews, ratings & moderation. |
| Service orders | `/api/service-orders` | Vehicle maintenance tracking. |
| Users | `/api/users` | Profiles & avatars. |
| Admin | `/api/admin` | Admin management of customers & vehicles. |

A `GET /api/health` endpoint is available for liveness checks.

## Project Structure

```
car-rental-system/
├── car-rental-frontend/      # Next.js app (App Router)
│   └── src/
│       ├── app/              # Routes: /, /register, /dashboard/**, …
│       ├── components/       # UI components, grouped per feature
│       ├── hooks/            # SWR-based data hooks
│       ├── contexts/         # Auth & settings providers
│       ├── types/            # TypeScript interfaces
│       ├── i18n/             # Translations
│       └── lib/              # API client & utilities
├── car-rental-backend/       # FastAPI app
│   ├── app/
│   │   ├── routers/          # Route handlers (auth, vehicles, …)
│   │   ├── services/         # Business logic (pricing, risk scoring, …)
│   │   ├── repositories/     # Data-access layer
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── db/               # PostgreSQL, MongoDB, Redis clients
│   │   ├── core/             # Security, deps, email, exceptions
│   │   └── config.py         # Settings
│   ├── alembic/              # Database migrations
│   ├── scripts/             # seed / init helpers
│   └── tests/                # pytest suite
├── e2e/                      # Playwright end-to-end tests
├── docs/                     # ERDs (PostgreSQL / MongoDB / Redis)
├── nginx/                    # Reverse-proxy config
└── docker-compose.yml        # Full-stack orchestration
```

## Testing

```bash
# Backend (pytest)
cd car-rental-backend && pytest

# Frontend (Jest + React Testing Library)
cd car-rental-frontend && npm test

# End-to-end (Playwright) — requires the stack to be running
cd e2e && npx playwright test
```
