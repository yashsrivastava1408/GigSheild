# CODEX.md

Project guidance for working on GigShield.

## What this project is

GigShield is a parametric micro-insurance platform for Indian gig delivery workers. The product protects weekly income loss caused by external disruptions such as heavy rain, floods, heat, AQI spikes, curfews, or zone outages.

Core constraints:
- Coverage is income loss only.
- Do not add health, life, accident, or vehicle repair insurance.
- Weekly pricing is mandatory.
- Persona focus should stay on one delivery segment per solution path, such as food delivery, grocery/q-commerce, or e-commerce delivery.

## Current product shape

The repo already contains a working full-stack MVP:
- FastAPI backend
- React + Vite frontend
- PostgreSQL-oriented data model with SQLite-based tests
- Mock-friendly integrations for OTP, weather, and payouts
- Worker and admin user journeys

Main flows already present:
- Worker registration and OTP login
- Weekly premium quote generation
- Policy purchase and policy listing
- Disruption event creation and weather sync
- Automatic claim creation from disruption events
- Manual review queue for claims
- Payout creation and settlement simulation
- Trust score recomputation
- Fraud log recording
- Admin operations for weather sync and policy expiry

## Architecture

- Backend entrypoint: `backend/app/main.py`
- API router: `backend/app/api/v1/router.py`
- Frontend entrypoint: `frontend/src/App.tsx`
- Worker UI: `frontend/src/components/WorkerDashboard.tsx`
- Admin UI: `frontend/src/components/AdminConsole.tsx`
- Auth flow UI: `frontend/src/components/AuthFlow.tsx`

Backend domains:
- `app/services/premium.py` for weekly pricing
- `app/services/claims.py` for claim and payout automation
- `app/services/trust.py` for trust-score computation
- `app/services/disruptions.py` for disruption ingestion
- `app/services/weather_sync.py` for mock/live weather signal sync
- `app/services/admin.py` for manual review operations
- `app/services/providers.py` for mock or live integrations

## Important product rules

- Weekly premium model is not optional. Do not change the billing concept to monthly or daily.
- Claims must remain parametric and tied to external triggers.
- Coverage must remain focused on lost income, not repair or medical reimbursement.
- Trust score and fraud logic may be improved, but keep the worker-facing explanation simple.
- Mock integrations are acceptable for the hackathon, but keep the mock/live switch clean in config.

## Environment assumptions

- Backend requires Python 3.11 or newer. The code and tests use `datetime.UTC`.
- Frontend expects Node.js with local dependencies installed before building.
- Backend config lives in `backend/app/core/config.py`.
- The app is designed to run through Docker, but local dev is supported.

## How to run

Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Full stack:
```bash
docker-compose up --build
```

## Testing and verification

Backend tests are in `backend/tests/`.

Useful coverage areas:
- `test_premium.py` for quote generation
- `test_policy_flow.py` for registration and policy purchase
- `test_claim_automation.py` for disruption-driven claims and payouts
- `test_auth_and_admin.py` for OTP, admin review, weather sync, and expiry
- `test_trust_score.py` for trust score logic

Current local caveat:
- If the local Python runtime is 3.10, pytest collection will fail because the tests import `datetime.UTC`.
- If frontend dependencies are missing, `npm run build` will fail because `tsc` is not installed.

## Coding conventions

- Prefer small, targeted changes over broad refactors.
- Keep API contracts aligned between backend schemas and `frontend/src/lib/api.ts`.
- Do not rename enums or response fields casually. The frontend depends on them.
- Use existing mock/provider toggles before introducing new infrastructure.
- Avoid adding new product areas that violate the hackathon statement.

## Hackathon priorities

If time is limited, prioritize:
1. Reliability of the current onboarding, quote, policy, claim, and payout loop.
2. Clear demo paths for worker and admin users.
3. Better fraud/risk explanation in the UI.
4. Real external integrations only after the demo flow is stable.

## What to preserve

- Weekly pricing language.
- Parametric trigger logic.
- Worker-first UX.
- Admin review capability.
- Mock-friendly demo mode.
- The current frontend/backend route shape.
