# Migration Plan — Build Order

The safest build order for Payout Engine. Each slice leaves the project in a working, deployable state.

---

## Slice 1: Foundation (S)
**Goal**: Django project boots, connects to Postgres, passes health check.

- [ ] `django-admin startproject config`
- [ ] Install: djangorestframework, psycopg2-binary, python-decouple, celery, redis
- [ ] Configure settings: DATABASE_URL, installed apps, DRF defaults
- [ ] `GET /api/v1/health/` returns `{"status": "ok"}`
- [ ] docker-compose up → all services healthy

---

## Slice 2: Merchant Model + Ledger (M)
**Goal**: Merchants exist, have bank accounts, and have a balance derived from ledger entries.

- [ ] `Merchant` model (id, name, email)
- [ ] `BankAccount` model (merchant FK, account_number, ifsc, is_active)
- [ ] `LedgerEntry` model (merchant FK, entry_type, amount_paise BigIntegerField, created_at)
- [ ] `MerchantService.get_balances(merchant)` → returns `{available, held}` via DB aggregation
- [ ] `seed_merchants` management command → 2-3 merchants with credit history
- [ ] `GET /api/v1/merchants/me/` → profile + balance
- [ ] `GET /api/v1/merchants/me/ledger/` → paginated entries
- [ ] Tests: balance invariant, no floats

---

## Slice 3: Payout Request API (M)
**Goal**: Merchants can request payouts. Concurrency and idempotency are correct.

- [ ] `Payout` model (all fields from PRD)
- [ ] `PayoutService.create_payout()` with `select_for_update()` + `transaction.atomic()`
- [ ] Idempotency check inside same transaction
- [ ] `POST /api/v1/payouts/` — all error cases handled
- [ ] Tests: happy path, insufficient balance, concurrent duplicate requests, idempotent repeat

---

## Slice 4: State Machine (S)
**Goal**: Status transitions are enforced at the model layer — no illegal moves possible.

- [ ] `Payout.transition_to(new_status)` raises `InvalidStateTransition` for illegal moves
- [ ] Tests: every legal transition, every illegal transition

---

## Slice 5: Celery Worker (M)
**Goal**: Payouts are processed asynchronously with simulated bank settlement.

- [ ] Celery + Redis configured
- [ ] `process_payout` task: pending → processing → completed/failed
- [ ] Simulate: 70% success, 20% fail, 10% hang
- [ ] Failed payout returns funds atomically
- [ ] Task is idempotent (guards on entry)
- [ ] Tests: mock simulation, verify fund return on failure

---

## Slice 6: Retry Logic (S)
**Goal**: Stuck payouts are automatically retried and eventually failed.

- [ ] Celery beat configured
- [ ] `retry_stuck_payouts` task runs every 10s
- [ ] Exponential backoff: 30s → 60s → 120s
- [ ] After 3 attempts → failed + funds returned
- [ ] Tests: simulate hang × 3, assert eventual failure + refund

---

## Slice 7: React Dashboard (M)
**Goal**: Merchant can see balance, ledger, and payout history in a UI.

- [ ] Vite + React + Tailwind scaffold
- [ ] `api/` layer with fetch wrappers
- [ ] `BalanceCard` component
- [ ] `LedgerTable` component
- [ ] `PayoutForm` component (amount in INR, converts to paise)
- [ ] `PayoutHistoryTable` with status badges
- [ ] 5-second polling for live updates
- [ ] Error states and loading states

---

## Slice 8: Hardening (L)
**Goal**: All invariants verified, edge cases covered, ready to demo.

- [ ] `check_invariants` management command
- [ ] Run `/test-concurrency` skill — all concurrency tests pass
- [ ] Run `/check-invariants` — all pass
- [ ] Add `README.md` with setup instructions
- [ ] Confirm zero FloatFields in codebase (`grep -r "FloatField" backend/`)