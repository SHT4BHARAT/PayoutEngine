# ADR 004: Celery + Redis for background payout processing

**Date**: 2026-04-27  
**Status**: Accepted

## Context
Payout processing must be async — we simulate bank settlement which takes time and can hang. Sync processing in the request cycle is explicitly forbidden.

## Decision
Use Celery with Redis as broker. One worker process handles payout processing tasks. Tasks are enqueued immediately when a payout is created.

## Task Design
- Task receives `payout_id` only — fetches fresh state from DB on execution
- Task is idempotent: checks current state before processing (guards against re-queue)
- Retry detection: if payout has been in `processing` > 30s and attempt_count < 3, re-queue
- Final failure: atomically set status=failed + return held funds in one transaction

## Consequences
- Requires Redis running (included in docker-compose)
- Celery beat needed for the stuck-payout retry sweep (runs every 10s)
- Task must handle the case where it's called on an already-completed payout (no-op)