# ADR 002: Use SELECT FOR UPDATE for concurrency control

**Date**: 2026-04-27  
**Status**: Accepted

## Context
Two concurrent payout requests can both read the same balance, both pass the check, and both deduct — resulting in a negative balance. This is the most common bug in payment systems.

## Decision
Every payout creation must:
1. Open `transaction.atomic()`
2. Lock the merchant row with `Merchant.objects.select_for_update().get(id=...)`
3. Compute balance using DB aggregation (`F()` expressions, `aggregate()`)
4. Only then check and deduct

## Consequences
- Concurrent requests serialize at the DB level — one waits for the other's lock
- Slightly higher latency on payout creation (acceptable — it's a write path)
- Eliminates check-then-act race condition entirely
- Must never compute balance in Python on already-fetched rows