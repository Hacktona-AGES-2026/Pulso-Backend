# Explainability

"Every decision must be explainable" is a fixed rule of the challenge, so this is part of the core.

Related: engine.md (where the numbers come from), ../ai/llm.md (what the LLM does).

## The receipt

Every patient gets a breakdown of why they are where they are. Example:

    Position 12 - Maria, 64, cholecystectomy
    Tier: B (upgraded: ER visit on 03/10)
    Score: 78
      +30 severity
      +22 deterioration (2 events in the last 30 days)
      +18 time (91% of max wait used)
      +8  predicted risk (P = 0.34)
    Ready to schedule: no (pre-anesthetic evaluation pending)

Same idea as reason codes in a credit score. The score is a sum of parts, so the receipt is exact.

## The deliverable's justificativa column

fila_priorizada.csv needs a justificativa on every row (~895).
Generate it from a deterministic template built from the receipt, e.g.:

    "A2 (neoplasia maligna C50.9); 3 meses na fila (prazo 21 dias); PS em 10/2026; risco 0.41"

Deterministic means reproducible, cheap and always consistent with the order. The LLM is used for longer explanations on demand.

## The LLM explains, it does not decide

The engine computes the order deterministically. The LLM extracts signals from text and writes explanations (details in ../ai/llm.md).
Not letting it decide keeps the order reproducible and auditable.

## Physician confirmation and overrides

- Tier changes proposed by the engine wait for a responsible physician to confirm.
- A physician can override a position with a written reason.
- Everything is logged (who, when, why, before/after) and shown on the receipt.

## Alerts

- Sudden deterioration: a patient jumps tiers -> alert to surgeon and nurse navigator.
- Patient about to pass the tier's max wait -> alert to regulation.
- Suspected malignancy with benign CID -> alert to review the CID.
