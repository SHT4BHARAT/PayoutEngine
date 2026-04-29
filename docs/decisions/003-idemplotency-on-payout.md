# ADR 003: Idempotency key stored on Payout model (not separate table)

**Date**: 2026-04-27  
**Status**: Accepted

## Context
Idempotency keys prevent duplicate payouts on network retries. We need to look up whether a key has been used and return the original response.

## Decision
Store `idempotency_key` and `idempotency_expires_at` directly on the `Payout` model. Unique constraint on `(merchant, idempotency_key)`. Lookup happens inside the same `transaction.atomic()` as creation to prevent TOCTOU race.

## Rejected Alternative
Separate `IdempotencyKey` table with a stored response blob. More flexible but overkill for MVP. The Payout *is* the response — no need to store it separately.

## Consequences
- Simple to implement and query
- Keys expire 24 hours after first use — a background task or DB-level cleanup can purge old ones
- Scoped per merchant: same UUID from two merchants = two independent keys