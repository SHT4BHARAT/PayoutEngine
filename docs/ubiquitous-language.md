# Ubiquitous Language — Payout Engine

A shared glossary for the domain. Use these terms consistently in code, comments, API responses, and conversation.

---

## Core Terms

**Merchant**  
An Indian agency or freelancer registered on Payout Engine. Has a balance, bank accounts, and can request payouts.

**Balance**  
A merchant's total funds on Payout Engine. Split into two sub-balances:
- **Available Balance** — funds the merchant can freely withdraw
- **Held Balance** — funds locked against a pending or processing payout

> `total_balance = available_balance + held_balance`

**Paise**  
The atomic unit of money in this system. 100 paise = 1 INR. All amounts stored and transmitted as integers in paise. Never converted to INR inside the backend.

**LedgerEntry**  
An immutable record of a money event on a merchant's account. Has a type:
- **Credit** — money added to the merchant (simulated customer payment)
- **Debit** — money locked or removed from the merchant (payout hold or settlement)

Balances are always derived from ledger entries, never stored independently.

**Payout**  
A merchant's request to withdraw funds to their bank account. Has a status and lifecycle. Money is held at creation and released (to bank or back to merchant) on completion or failure.

**Payout Status**  
The current state of a payout in its lifecycle:
- `pending` — created, funds held, not yet picked up by worker
- `processing` — worker has picked it up and is awaiting bank response
- `completed` — bank settled successfully, funds disbursed
- `failed` — bank rejected or timeout after max retries, funds returned

**Idempotency Key**  
A merchant-supplied UUID sent in the `Idempotency-Key` HTTP header. Guarantees that submitting the same payout request twice produces the same result and only one payout. Scoped per merchant, expires after 24 hours.

**Hold**  
The act of moving funds from available balance to held balance when a payout is created. Reversed (released) if the payout fails. Completed if the payout succeeds.

**Settlement**  
The simulated bank transfer that moves funds from Payout Engine to the merchant's Indian bank account. Succeeds 70%, fails 20%, hangs 10% of the time.

**Stuck Payout**  
A payout that has been in `processing` state for more than 30 seconds without a resolution. Triggers automatic retry with exponential backoff.

**Bank Account**  
An Indian bank account belonging to a merchant, identified by account number and IFSC code. Payouts are disbursed to a specific bank account.

---

## What to Avoid

| Avoid | Use instead |
|-------|-------------|
| "wallet" | "balance" or "ledger" |
| "transfer" | "payout" (merchant withdrawing) or "credit" (customer paying) |
| "transaction" | "ledger entry" or "payout" (be specific) |
| "rupees" in code | "paise" — rupees only for display |
| "withdraw" | "request a payout" |
| "account balance" | "available balance" (be explicit about type) |