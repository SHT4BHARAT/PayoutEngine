# Codebase Tour — Payout Engine

A guide for anyone new to this codebase. Read this before touching any code.

---

## Folder Structure

```
payout-engine/
├── backend/
│   ├── config/              Django project settings, URL root, Celery config
│   ├── merchants/           Merchant model, bank accounts, ledger
│   ├── payouts/             Payout model, state machine, API views, idempotency
│   ├── workers/             Celery tasks — payout processor, retry sweep
│   ├── common/              Shared: money utils, error codes, base classes
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── api/             fetch wrappers for every endpoint
│       ├── components/      dumb UI: BalanceCard, PayoutRow, StatusBadge
│       ├── pages/           Dashboard (the only page for MVP)
│       └── hooks/           useBalance, usePayouts, usePolling
│
├── docker-compose.yml       postgres + redis + backend + celery + frontend
├── .env.example
├── CLAUDE.md                ← read this first
└── docs/
    ├── prd.md
    ├── ubiquitous-language.md
    └── decisions/
```

---

## Request Lifecycle: Creating a Payout

Trace of `POST /api/v1/payouts/`:

```
1. PayoutCreateView.post()
   └── Validates Idempotency-Key header present

2. PayoutCreateSerializer.validate()
   └── Checks amount > 0, bank_account belongs to merchant

3. PayoutService.create_payout()  ← the critical path
   ├── transaction.atomic()
   ├── Merchant.objects.select_for_update().get(id=...)  ← row lock
   ├── compute available_balance via DB aggregation
   ├── if balance < amount → raise InsufficientBalanceError
   ├── check for existing idempotency key → return existing payout if found
   ├── Payout.objects.create(status='pending', ...)
   ├── LedgerEntry.objects.create(type='debit', ...)  ← hold
   └── commit

4. process_payout.delay(payout_id)  ← enqueue Celery task

5. Return 201 (or 200 if idempotent repeat)
```

---

## Background Worker Lifecycle

```
workers/tasks.py → process_payout(payout_id)

1. Fetch payout, check status == 'pending' (guard: no-op if already processing/done)
2. Atomically set status = 'processing', record attempt_count++
3. Simulate bank settlement:
   - random() < 0.70 → succeed
   - random() < 0.90 → fail
   - else → hang (return without resolving)
4. On success:
   - transaction.atomic()
   - status = 'completed'
   - LedgerEntry(type='debit', finalized)  ← settlement confirmed
5. On failure:
   - transaction.atomic()
   - status = 'failed'
   - LedgerEntry(type='credit', ...)  ← funds returned
6. On hang → celery beat sweep picks it up after 30s
```

---

## Where the Important Logic Lives

| What | Where |
|------|-------|
| Balance calculation | `merchants/services.py → get_balances()` |
| Payout creation + hold | `payouts/services.py → create_payout()` |
| Idempotency check | Inside `create_payout()` — same transaction as creation |
| State machine enforcement | `payouts/models.py → Payout.transition_to()` |
| Bank simulation | `workers/tasks.py → simulate_bank_settlement()` |
| Retry sweep | `workers/tasks.py → retry_stuck_payouts()` — runs every 10s via beat |
| Money formatting | `common/money.py → paise_to_inr_display()` |

---

## Non-Obvious Gotchas

**Never compute balance in Python.** Always use:
```python
from django.db.models import Sum, F
balance = LedgerEntry.objects.filter(merchant=merchant).aggregate(
    total=Sum('amount_paise', filter=Q(entry_type='credit')) -
          Sum('amount_paise', filter=Q(entry_type='debit'))
)['total'] or 0
```

**The Celery task must be idempotent.** It checks status on entry — if a payout is already `completed` or `failed`, it returns immediately. This handles re-queued tasks safely.

**Idempotency lookup is inside the transaction.** If it were outside, two concurrent calls with the same key could both miss the lookup and both create a payout.

**State transitions raise, not return.** `payout.transition_to('completed')` raises `InvalidStateTransition` if the move is illegal. Never catch this silently.