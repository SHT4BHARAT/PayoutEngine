# Playto Payout Engine

A robust, concurrency-safe payout engine built with Django, Celery, and React. 
This engine is designed to handle high-concurrency requests, enforce strict idempotency, and never drop a single paise.

## Core Features
1. **Zero-Float Math**: All monetary amounts are stored and calculated strictly as integers (paise) at the database layer. No floating-point inaccuracies.
2. **Strict Concurrency Guards**: Uses `select_for_update()` to enforce row-level locking during balance checks and deductions, entirely preventing double-spending race conditions.
3. **Idempotency Checks**: Every payout request requires a unique `Idempotency-Key` header to safely handle network retries.
4. **State Machine Integrity**: Django model lifecycle hooks rigidly enforce `pending -> processing -> completed/failed` state transitions.
5. **Background Workers & Retries**: Celery workers simulate upstream bank settlements. A Celery beat task runs a sweeper to apply exponential backoff to stuck `processing` tasks and retry them.
6. **Real-Time React Dashboard**: A Tailwind-powered frontend utilizing 5-second polling to reflect live balances, ledger entries, and payout statuses.

## Setup Instructions

### 1. Backend (Django + Celery)

**Prerequisites:** Python 3.10+, Redis server running on `localhost:6379`.

```bash
cd backend
python -m venv venv

# On Mac/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate

pip install -r requirements.txt

# Migrate and Seed the database
python manage.py migrate
python manage.py seed_merchants

# Start the Django server
python manage.py runserver
```

In new terminal windows, start the Celery worker and beat scheduler (ensure Redis is running, e.g., `docker-compose up -d redis`):
```bash
cd backend
# Activate venv again (Mac/Linux): source venv/bin/activate 
# Activate venv again (Windows): .\venv\Scripts\activate

# On Mac/Linux:
celery -A config worker -l info
# On Windows (avoids multiprocessing PermissionError):
celery -A config worker -l info --pool=solo

# In another terminal:
cd backend
# Activate venv again (Mac/Linux): source venv/bin/activate 
# Activate venv again (Windows): .\venv\Scripts\activate
celery -A config beat -l info
```

### 2. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## Testing & Hardening

Run the test suite (includes threading-based concurrency tests):
```bash
cd backend
python manage.py test merchants payouts workers
```

Run the invariant checker (verifies that ledger sums exactly match derived balances with no money leaks):
```bash
cd backend
python manage.py check_invariants
```