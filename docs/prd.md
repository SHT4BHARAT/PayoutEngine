# PRD: Payout Engine — Minimal Viable Product

**Version**: 1.0  
**Status**: Final  
**Last Updated**: 2026-04-27

---

## Overview

Payout Engine is a fintech service for Indian agencies and freelancers who receive international payments. The product collects USD from international customers and disburses INR to merchant Indian bank accounts. This PRD covers the payout engine MVP — the component that manages merchant balances and processes withdrawal requests.

---

## Goals

- Allow merchants to see their real-time available and held balance
- Allow merchants to request a payout to their bank account
- Process payouts asynchronously with real lifecycle management
- Never lose or double-spend money under any condition
- Demonstrate correctness under concurrency, not just happy-path flows

## Non-Goals

- Customer payment collection (USD inflow) — simulated via seed data
- KYC / AML compliance
- Real bank API integration — settlement is simulated
- Multi-currency support
- Admin panel beyond what Django admin provides

---

## Users

**Merchant** — An Indian agency or freelancer. Has an account, a bank account on file, a balance in paise, and can request payouts.

---

## User Stories

### Ledger
- As a merchant, I can see my available balance and held balance in INR so I know what I can withdraw.
- As a merchant, I can see a chronological list of all credits (customer payments) and debits (payouts) on my account.
- As a merchant, my balance is always consistent — it always equals credits minus debits, no matter what happens concurrently.

### Payout Requests
- As a merchant, I can request a payout by specifying an amount and my bank account.
- As a merchant, if I accidentally submit the same payout request twice (network retry), only one payout is created and I get the same response both times.
- As a merchant, if I don't have enough available balance, my payout request is rejected immediately with a clear error.
- As a merchant, if two concurrent requests exceed my balance, exactly one is accepted and the other is rejected — never both.

### Payout Tracking
- As a merchant, I can see the status of all my payouts: pending, processing, completed, or failed.
- As a merchant, if my payout fails, my funds are immediately returned to my available balance.
- As a merchant, the dashboard updates without me refreshing the page.

---

## Technical Requirements

### Data Model

**Merchant**
```
id, name, email, created_at
```

**BankAccount**
```
id, merchant (FK), account_number, ifsc_code, account_holder_name, is_active
```

**LedgerEntry**
```
id, merchant (FK), entry_type (credit | debit), amount_paise (BigInt),
reference_id, description, created_at
```

**Payout**
```
id, merchant (FK), bank_account (FK), amount_paise (BigInt),
status (pending | processing | completed | failed),
idempotency_key, idempotency_expires_at,
held_at, processed_at, completed_at, failed_at,
failure_reason, attempt_count, created_at, updated_at
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/merchants/me/` | Current merchant profile + balance |
| GET | `/api/v1/merchants/me/ledger/` | Paginated ledger entries |
| POST | `/api/v1/payouts/` | Request a payout (idempotency required) |
| GET | `/api/v1/payouts/` | List payouts with status |
| GET | `/api/v1/payouts/{id}/` | Single payout detail |

### Payout Request
```http
POST /api/v1/payouts/
Idempotency-Key: <merchant-supplied UUID>
Content-Type: application/json

{
  "amount_paise": 50000,
  "bank_account_id": "uuid"
}
```

Response (201 Created or 200 OK on repeat):
```json
{
  "id": "uuid",
  "amount_paise": 50000,
  "status": "pending",
  "idempotency_key": "...",
  "created_at": "..."
}
```

Error responses:
```json
{ "error": "Insufficient available balance", "code": "insufficient_balance" }
{ "error": "Amount must be greater than zero", "code": "invalid_amount" }
{ "error": "Bank account not found", "code": "bank_account_not_found" }
{ "error": "Idempotency-Key header is required", "code": "missing_idempotency_key" }
```

---

## Payout Lifecycle

```
[POST /api/v1/payouts/]
        ↓
   pending  ←──── idempotent: same key returns same response
        ↓
   (Celery picks up)
        ↓
  processing
     ↙      ↘
completed   failed
            ↓
     funds returned to merchant (atomic)
```

**Simulation probabilities** (in Celery worker):
- 70% → completed
- 20% → failed (funds returned)
- 10% → stays in processing (simulate hang → triggers retry)

**Retry logic**:
- Payouts in `processing` > 30 seconds → retry
- Exponential backoff: 30s → 60s → 120s
- After 3 failed attempts → move to `failed`, return funds atomically

---

## Concurrency Design

Every payout creation must:
1. Open `transaction.atomic()`
2. `SELECT ... FOR UPDATE` on Merchant row (row-level lock)
3. Compute available balance using DB aggregation
4. Reject if balance < requested amount
5. Create Payout (pending) + LedgerEntry (debit, held) in same transaction
6. Commit

This guarantees that two concurrent requests cannot both pass the balance check.

---

## Idempotency Design

- Key is merchant-scoped (same key from two merchants = two different keys)
- Key expires 24 hours after first use
- On duplicate key: return exact same response body + same HTTP status (200, not 201)
- Keys stored on the Payout model itself (no separate table needed for MVP)
- Lookup by `(merchant_id, idempotency_key)` inside the same `transaction.atomic()` as creation

---

## Frontend Requirements

**Dashboard page** (`/dashboard`)
- Available balance (INR, formatted ₹X,XX,XXX.XX)
- Held balance (INR)
- Total balance = available + held
- Recent ledger entries (last 10, with amount, type, date)

**Payout form**
- Amount input (in INR — convert to paise before API call)
- Bank account selector (pre-populated from merchant's accounts)
- Submit button with loading state
- Clear error display on rejection

**Payout history table**
- Columns: Date, Amount, Status, Bank Account
- Status badge: color-coded (pending=yellow, processing=blue, completed=green, failed=red)
- Auto-refresh every 5 seconds (polling)

---

## Seed Data

On `python manage.py seed_merchants`:
- Create 2–3 merchants with email + token auth
- Each merchant gets 1 bank account
- Each merchant gets 5–10 credit ledger entries (simulated customer payments)
- Starting balances should be meaningful: e.g., ₹10,000 / ₹25,000 / ₹5,000

---

## Acceptance Criteria

- [ ] Balance invariant holds: `SUM(credits) - SUM(debits) == displayed balance` at all times
- [ ] Concurrent duplicate requests: exactly one succeeds, other gets 402
- [ ] Idempotent requests: same response returned, one DB row
- [ ] Illegal state transitions rejected at model layer
- [ ] Failed payout returns funds in same DB transaction as status update
- [ ] Celery processes payouts (not sync)
- [ ] Stuck payouts retried with backoff, failed after 3 attempts
- [ ] React dashboard shows live status updates
- [ ] All money stored as integers (paise) — zero floats in codebase

---

## Open Questions

- ~~Float vs integer for money?~~ → Resolved: BigIntegerField in paise always
- ~~Which background job library?~~ → Resolved: Celery + Redis
- ~~Idempotency: separate table or on Payout model?~~ → Resolved: on Payout model for MVP
- Real-time updates: polling vs WebSocket? → Polling (5s interval) for MVP. WebSocket stretch goal.