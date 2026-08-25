> ## ⚠️ INTENTIONALLY NON-COMPLIANT — SVORAH TEST FIXTURE
>
> This repository is a **deliberately DPDP-non-compliant test fixture** used to validate
> [SVORAH](https://svorah.com)'s compliance scanner. It is a real open-source Django banking app
> seeded with **DPDP Act (2023) violations** (plaintext Aadhaar/PAN, full card + CVV storage, PII in
> logs and URLs, raw PII sent to an LLM, bulk export, IDOR, hardcoded secrets, and more).
> See **[`GROUND_TRUTH.md`](GROUND_TRUTH.md)** for the full answer key.
>
> **Do not deploy this. Do not use this code as a reference for real systems.**
> All secrets, keys, and personal/financial data here are **fake placeholders** for scanner testing.
>
> **Base project:** forked from
> [`saadmk11/banking-system`](https://github.com/saadmk11/banking-system) and modified by seeding
> compliance violations. Original README below.

---

# Banking System

A banking system project built with Django. (Original project by
[saadmk11](https://github.com/saadmk11/banking-system).)

## Features

- User registration and bank-account creation
- Deposit / withdraw with interest calculation
- Transaction reports
