# Technical architecture

Related: ../product/vision.md (why the event log), ../prioritization/engine.md (what the engine computes).

## Big picture

    Sources (HIS adapters, WhatsApp, forms, scheduling)
      -> event log (append-only)
        -> features as of a date (data/build_features.py)
          -> prioritization engine (policy vX: tiers + score + JEV risk)
            -> queue snapshot + receipts
              -> fila_priorizada.csv (deliverable)
              -> API -> role views / alerts / LLM explanations
              -> audit, simulation, shadow mode

## Components

- Event log: the dataset's eventos_clinicos.csv plus new events posted by the views (calls, check-ins, confirmations). Append-only.
- Features: data/build_features.py, already builds everything "as of" any date.
- Engine: standalone, testable Python module. features -> tiers -> score -> ordering -> receipts. Takes a policy (weights + rules) as input.
- JEV: model trained on out/train_h90.csv (../ai/jev.md).
- LLM service: text extraction with evidence, explanations, agent reviews (../ai/llm.md). Results cached.
- API: serves the engine to the frontend.
- Frontend: role views (../product/frontend.md). No prioritization logic in the frontend.

## API (first cut)

- GET  /queue?asof=YYYY-MM-DD&policy=v1      ordered queue with tier, score, readiness
- GET  /patients/{solicitacao_id}?asof=...    receipt, events, Monte Carlo range
- POST /events                                 add an event (call result, check-in, ER visit)
- POST /confirmations                          physician confirms or rejects a tier change, with reason
- GET  /policies, POST /policies/{v}/shadow   policy versions and shadow-mode diff
- GET  /simulation?policy=...                  before/after numbers

## Stack

- Python: pandas for data, scikit-learn for JEV v1.
- FastAPI for the API.
- Frontend: React (Next.js or Vite) for the role views; Streamlit multipage as a fallback if frontend time is short.
- LLM only for extraction, explanations and agent reviews. The data is synthetic, so an external API is fine.

## Principles

- Deterministic engine: same events + same policy = same order.
- Every ordering records the policy version and the "as of" date.
- If the engine fails, views keep working from the last snapshot.
