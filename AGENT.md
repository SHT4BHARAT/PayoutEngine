# Payout Engine

## What this is
A backend-heavy fintech service that lets Indian agencies and freelancers receive international payments. Money flows one way: international customer → Payout (USD) → merchant bank account (INR). This project focuses on the payout engine: the piece that holds merchant balances and processes withdrawals to Indian bank accounts.

This is a graded engineering challenge. Features are secondary. Correctness under concurrency, idempotency, and data integrity are what matter.

---

## Tech Stack
- **Backend**: Django 4.x + Django REST Framework
- **Frontend**: React 18 + Tailwind CSS + Vite
- **Database**: PostgreSQL (required — use select_for_update, atomic transactions)
- **Background Jobs**: Celery + Redis (no sync faking)
- **Auth**: Token-based (DRF TokenAuth) — keep it simple
- **Containerization**: Docker + docker-compose

---

## How to run locally
```bash
cp .env.example .env          # fill in secrets
docker-compose up -d          # postgres + redis
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_merchants   # seeds 2-3 merchants with credit history
python manage.py runserver

# In another terminal
celery -A config worker -l info

# Frontend
cd frontend
pnpm install
pnpm dev
```

---

## Project Conventions

### Money
- ALL amounts in **paise** (integer). 1 INR = 100 paise.
- Use `BigIntegerField` everywhere. **Never** FloatField. **Never** DecimalField.
- **Never** do arithmetic in Python on fetched rows. Always use `F()` expressions and DB-level aggregation.
- Balance = SUM(credits) - SUM(debits) always. This invariant is checked by tests.

### Database
- Use `select_for_update()` on Merchant row before any balance check or deduction.
- All payout creation + balance hold must happen inside `transaction.atomic()`.
- State transitions must be atomic with any side effects (e.g., returning funds on failure).

### API
- Versioned under `/api/v1/`
- All money fields returned as integers (paise). Frontend converts for display.
- Idempotency-Key header required on `POST /api/v1/payouts/`
- Standard DRF error format: `{ "error": "...", "code": "..." }`

### Background Jobs
- Celery workers handle payout processing — no sync code.
- Payouts stuck in `processing` > 30 seconds → retry with exponential backoff.
- Max 3 retries → move to `failed`, return funds atomically.
- Task must be idempotent — re-running it should not double-process.

### State Machine
```
pending → processing → completed
pending → processing → failed (funds returned atomically)
```
Any other transition must raise an error. Enforce at the model level, not just the view.

### Frontend
- Balance displayed in INR (divide paise by 100), formatted as ₹X,XX,XXX.XX
- Poll payout status every 5 seconds or use WebSocket (Celery → Django Channels optional)
- No money calculations in JS — display only

---

## Folder Ownership
```
backend/
  config/           → Django settings, urls, celery config
  merchants/        → Merchant model, balance logic, ledger entries
  payouts/          → Payout model, state machine, idempotency, API views
  workers/          → Celery tasks for payout processing
  common/           → Shared utilities (money formatting, errors)

frontend/
  src/
    api/            → All fetch calls, typed
    components/     → Dumb UI components
    pages/          → Dashboard, PayoutForm, PayoutHistory
    hooks/          → useBalance, usePayouts, usePolling
```

---

## What NOT to do
- Never fake async work with `time.sleep()` in the request cycle
- Never store money as float anywhere in the codebase
- Never check balance and then deduct in separate queries (race condition)
- Never allow a state transition that isn't in the legal state machine
- Never create a duplicate payout for the same idempotency key
- Never do balance arithmetic in Python — always use DB aggregation

---

## Key Invariants (Tested)
1. `merchant.available_balance + merchant.held_balance == SUM(all credits) - SUM(all completed/failed debits)`
2. Two concurrent 60 rupee requests against 100 rupee balance → exactly one succeeds
3. Same idempotency key called twice → identical HTTP response, one DB row
4. No payout transitions outside the legal state machine
5. A failed payout always returns its held funds (never leaks)

---

## Current Focus
Building the MVP. Priority order:
1. Merchant model + ledger (foundation everything else sits on)
2. Payout request API with idempotency
3. Celery worker with simulated bank settlement
4. State machine enforcement
5. React dashboard

---

## Decisions Log
See `docs/decisions/` for Architecture Decision Records.