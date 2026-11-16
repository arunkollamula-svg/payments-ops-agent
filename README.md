# Payments Ops Agent

An AI agent that investigates payment reconciliation mismatches between
gateway status (KNET, MPGS, Apple Pay) and the internal ledger of an eWallet.

## Problem
In payment operations, a transaction can succeed at the gateway but stay
pending in the ledger (customer charged, not credited), or fail at the
gateway but get posted (merchant over-credited). Ops teams find these
manually. This agent finds, prioritises, and explains them.

## Design decisions
- **Business rules in code, not in the LLM.** Severity and issue type are
  computed deterministically in SQL. The LLM investigates and explains.
- **Read-only agent.** It can only recommend refunds or reversals, never
  execute them.
- **Model-agnostic.** Uses the OpenAI-compatible API, so it runs on Groq or
  any compatible provider by changing one setting.
- **Defensive tool handling.** Junk tool arguments from the model are
  filtered; the agent loop is bounded; rate limits are retried with backoff.

## Stack
Python, PostgreSQL, Groq (openai/gpt-oss-120b), OpenAI SDK

## Run locally (Windows)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # then add your Groq API key
psql -U postgres -h localhost -f schema.sql
python agent.py
```

## Sample output
```
1. TXN1003 - MERCHANT_OVERCREDITED (CRITICAL) - KWD 150.750
2. TXN1002 - CUSTOMER_NOT_CREDITED (MEDIUM) - KWD 12.000
```

## Roadmap
- [ ] Human approval workflow for reversals
- [ ] FastAPI service
- [ ] Evaluation test suite
- [ ] Cloud deployment