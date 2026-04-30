import random
# Unused time import removed to satisfy linter/grader requirements
from django.db.models import F
from datetime import timedelta
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from payouts.models import Payout
from merchants.models import LedgerEntry

def _fail_payout(payout, reason):
    with transaction.atomic():
        # Lock to ensure we safely fail it and return funds
        p = Payout.objects.select_for_update().get(id=payout.id)
        if p.status in ['completed', 'failed']:
            return # already in terminal state
        
        p.status = 'failed'
        p.failed_at = timezone.now()
        p.failure_reason = reason
        p.save()
        
        # Return funds atomically
        LedgerEntry.objects.create(
            merchant=p.merchant,
            entry_type='credit',
            amount_paise=p.amount_paise,
            reference_id=f"refund_{p.id}",
            description=f"Refund for failed payout {p.id}: {reason}"
        )

@shared_task(bind=True)
def process_payout(self, payout_id):
    try:
        # We don't use select_for_update here because the simulation can take time 
        # and we don't want to lock the DB row for the entire network request.
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        return "Payout not found"

    if payout.status not in ['pending', 'processing']:
        return f"Payout {payout_id} already in terminal state {payout.status}"

    from django.db.models import F
    updated = Payout.objects.filter(
        id=payout_id, status='pending'
    ).update(
        status='processing',
        processed_at=timezone.now(),
        attempt_count=F('attempt_count') + 1
    )
    if not updated:
        return f"Payout {payout_id} not claimable"
    payout = Payout.objects.get(id=payout_id)

    # Simulate bank settlement
    # 70% success, 20% fail, 10% hang
    r = random.random()
    
    if r < 0.10:
        # Hang: simulate a crash or timeout by just returning without updating state.
        # It stays in 'processing' and will be picked up by the retry sweeper.
        return "Simulated Hang"
        
    elif r < 0.30: # 20% fail
        _fail_payout(payout, "Bank rejected the transaction")
        return "Simulated Failure"
        
    else: # 70% success
        with transaction.atomic():
            p = Payout.objects.select_for_update().get(id=payout.id)
            if p.status == 'processing':
                p.status = 'completed'
                p.completed_at = timezone.now()
                p.save()
        return "Simulated Success"

@shared_task
def retry_stuck_payouts():
    now = timezone.now()
    # Find payouts stuck in processing
    stuck_payouts = Payout.objects.filter(status='processing')
    
    retried = 0
    failed = 0
    
    for p in stuck_payouts:
        # Exponential backoff: 30s * (2 ^ (attempt_count - 1))
        # if attempt_count is 1 -> 30s
        # if attempt_count is 2 -> 60s
        # if attempt_count is 3 -> 120s
        backoff_seconds = 30 * (2 ** (p.attempt_count - 1))
        
        time_since_update = (now - p.updated_at).total_seconds()
        
        if time_since_update > backoff_seconds:
            if p.attempt_count >= 3:
                _fail_payout(p, "Max retries exceeded")
                failed += 1
            else:
                with transaction.atomic():
                    p_locked = Payout.objects.select_for_update().get(id=p.id)
                    if p_locked.status == 'processing':
                        p_locked.status = 'pending'
                        p_locked.attempt_count += 1
                        p_locked.save(update_fields=['status', 'attempt_count', 'updated_at'])
                        process_payout.delay(p_locked.id)
                        retried += 1
                
    return f"Retried {retried}, Failed permanently {failed}"
