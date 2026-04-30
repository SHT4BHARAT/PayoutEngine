# Payout Engine Architecture & Design Decisions

This document outlines the core technical decisions made while building the Playto Payout Engine backend, specifically focusing on consistency, idempotency, and fault tolerance in the highly concurrent payment environment.

## 1. Concurrency Control & Double-Spend Prevention

To guarantee that a merchant cannot double-spend their balance, the system utilizes strict database-level locking:
*   **Pessimistic Locking (`select_for_update`)**: When a payout is created, the `Merchant` record is locked using `select_for_update()`. This ensures that if two concurrent requests attempt to create a payout for the same merchant, they are processed serially.
*   **Balance Calculation via Aggregation**: We never store a mutable `balance` integer directly on the `Merchant` model. Instead, the available balance is calculated in real-time by aggregating the sum of `credits` and `debits` from the immutable `LedgerEntry` append-only table.

## 2. Worker Race Condition Prevention

In a distributed environment, Celery workers can inadvertently pick up the same task multiple times (e.g., if a task is re-queued during a network partition before the first worker finishes). 
*   **Atomic Check-And-Set (CAS)**: To prevent a payout from being processed twice, we use an atomic `update()` query to transition the status from `pending` to `processing`.
    ```python
    updated = Payout.objects.filter(id=payout_id, status='pending').update(...)
    if not updated:
        return "Not claimable"
    ```
    This guarantees that exactly one worker thread "claims" the payout.

## 3. Strict State Machine Enforcement

The `Payout` model overrides its `__init__` and `save` methods to enforce strict state transitions and prevent N+1 query performance hits.
*   **Cached Original State**: The `__init__` method caches the `_orig_status`. When `save()` is called, we validate the transition (e.g., `pending` -> `processing`, `processing` -> `completed` / `failed`) without requiring an extra database lookup.
*   Illegal transitions instantly raise an `InvalidStateTransition` exception.

## 4. Idempotency

To prevent accidental double-charges from network retries on the client side:
*   **Unique Constraint**: The database enforces a `unique_together` constraint on `(merchant, idempotency_key)`.
*   **Expiry**: Idempotency keys are valid for 24 hours. The service layer strictly filters by `idempotency_expires_at__gt=timezone.now()`. If an old key is used after 24 hours, it is treated as a new unique transaction.

## 5. Fault Tolerance & Retry Logic

*   **Transaction Atoms**: All balance mutations and state changes are wrapped in `transaction.atomic()` blocks.
*   **Delayed Enqueuing**: Celery tasks are only queued using `transaction.on_commit()`. This guarantees the worker cannot attempt to process a payout before the database transaction creating that payout has fully committed.
*   **Retry Sweeper**: A periodic Celery beat task (`retry_stuck_payouts`) sweeps for payouts stuck in the `processing` state. It implements an exponential backoff algorithm and resets the payout back to `pending` before re-enqueuing it, allowing it to correctly traverse the state machine again up to a maximum of 3 attempts.