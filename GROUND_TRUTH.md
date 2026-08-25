# GROUND TRUTH — svorah-fixture-fintech

> Answer key for this fixture. Every row is a DPDP violation **deliberately planted** into a real
> open-source Django banking app, to test SVORAH's detection.
> Score a scan as: **recall** = planted violations detected / 21 · **precision** = true findings / all findings.

**Base repo:** `saadmk11/banking-system` (forked, then seeded).
**Stack:** Python · Django · PostgreSQL.
**Planted count:** 21 PRESENCE violations.

## Structural (sensitive fields / defaults — schema & pattern rules)

| # | Cat | DPDP | Sev | File | Where | What was planted |
|---|-----|------|-----|------|-------|------------------|
| 1 | A3 | S.6(1) | High | `accounts/models.py:145` | `share_with_partners` (+ `marketing_consent`:144) | Data-sharing / marketing opt-in default `True` |
| 2 | D3 | S.4(2) | Critical | `accounts/models.py:138,139` | `card_number`, `cvv` | Full card number **and CVV** stored (CVV must never be stored) |
| 3 | E1 | S.8(5) | High | `accounts/models.py:135` | `bank_account_number` | Bank account number stored plaintext |
| 4 | E3 | S.8(5) | Critical | `accounts/models.py:133,134` | `aadhaar`, `pan` | Aadhaar & PAN stored plaintext, unmasked |
| 5 | D1 | S.4(2) | High | `accounts/models.py:133-140` + `views.py:87` | KYC fields | Aadhaar + PAN + salary slip + income collected at onboarding (excessive) |
| 6 | G3 | S.8(7) | Medium | `accounts/models.py:147` | `is_active` | Soft-delete marker — accounts deactivated, all PII retained |

## Flows (source → sink — taint rules)

| # | Cat | DPDP | Sev | File | Where | Source → sink |
|---|-----|------|-----|------|-------|---------------|
| 7 | A1 | S.6 | High | `accounts/views.py:87` | `SubmitKYCView.post` | KYC PII persisted with no consent requested/recorded |
| 8 | A6 | S.6(4) | Critical | `accounts/integrations.py:28,18` | `nightly_bureau_sync` | Pushes **all** customers' PAN to the bureau — `consent_withdrawn` never checked |
| 9 | C1 | S.4/6 | High | `accounts/integrations.py:35` | `send_loan_offer` | Phone captured for login OTP reused for loan-marketing SMS |
| 10 | E2 | S.8(5) | Critical | `accounts/integrations.py:73` | `legacy_hash_password` | Passwords hashed with unsalted SHA1 |
| 11 | E4 | S.8(5) | High | `transactions/views.py:95` | `DepositMoneyView.form_valid` | Full card number + bank account written to logs |
| 12 | E5 | S.8(5) | High | `accounts/views.py:113,115` | `KYCVerifyView.get` | PAN + Aadhaar accepted as URL query params (and logged) |
| 13 | F1 | S.8(5) | Critical | `accounts/integrations.py:65` (called `transactions/views.py:97`) | `categorise_transaction` | Customer name + email + narration sent raw to OpenAI. Recipient=OpenAI → **suspected** cross-border (§16 deferred) |
| 14 | F2 | S.6/8 | High | `accounts/integrations.py:41` (called `transactions/views.py:100`) | `track_transaction` | `user.id` + email sent to a third-party analytics SDK per transaction |
| 15 | F3 | S.8(5) | High | `accounts/integrations.py:51,14` | `upload_kyc_document` | KYC docs → S3. Recipient=AWS S3, literal region hint `us-east-1` → **suspected** cross-border (§16 deferred) |
| 16 | F4 | S.8 | High | `accounts/views.py:150` | `ExportUsersView.get` | Bulk CSV of every customer: email, Aadhaar, PAN, card, CVV, account — no masking |
| 17 | K3 | S.8(5) | Critical | `accounts/views.py:120` | `InternalUserView.get` | Unauthenticated endpoint returns full KYC (Aadhaar/PAN/card/CVV) |
| 18 | K4 | S.8(5) | Critical | `accounts/views.py:135` | `AccountStatementView.get` | No ownership check — any logged-in user reads any account's statement (IDOR) |

## Config & hygiene

| # | Cat | DPDP | Sev | File | Where | What was planted |
|---|-----|------|-----|------|-------|------------------|
| 19 | E7 | S.8(5) | Critical | `banking_system/settings.py:26-29` | config | Hardcoded OpenAI / payment-gateway / AWS keys (plus pre-existing Django `SECRET_KEY`:23) |
| 20 | K2 | S.8(5) | Critical | `.env` | repo root | `.env` with DB creds + API keys committed to VCS |
| 21 | K1 | S.8(5) | High | `accounts/seed_data.py` | seed | Realistic customer PII (Aadhaar, PAN, card numbers) committed |

## Notes
- All secrets, keys, and personal/financial data are **fake** placeholders — no real credentials or people.
- **Cross-border (§16):** F1/F3 are marked **suspected** only (recipient named, plus a literal region
  hint for F3). The code agent does not *confirm* residency — that verdict belongs to the cloud scan,
  a declaration, or the DPO. Same rule as `svorah-test-repo`.
- ABSENCE-class violations (no consent record, no erasure endpoint, no retention TTL, no audit log) are
  intentionally **not** planted in this phase.
