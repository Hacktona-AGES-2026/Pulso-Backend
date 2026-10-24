# Prioritization engine

Rules decide the tier, the score orders patients inside a tier, and the risk model (JEV) is one input to the score.
Readiness is a separate dimension that never lowers priority.

Related: ../data/analysis.md (cleaning), ../ai/jev.md (risk score), explainability.md, robustness.md.

## Step 0 - Clean the data (done: ../data/build_features.py)

- Normalize CID (upper case, no dot), priority spelling, municipality.
- Merge 22 duplicate requests (keep the earliest entry, move events and text to it).
- Remove 24 requests that left the queue (13 gave up, 5 operated elsewhere, 6 found only in observacoes).
- Drop orphan and duplicated events.
- Rebuild the manual flags (oncologic, diabetic, worsening) from CID, events and text.
- Result: 895 active requests.

## Layer 1 - Tiers (SWALIS, hard rules)

| Tier | Max wait | Rule |
|---|---|---|
| A1 | 15 days | C* CID plus a progression sign (imaging progression, ER visit or hospitalization, text: crescimento rapido, linfonodo fixo, perda ponderal, disfagia, hemoptise); urgent CIDs I20.0, K40.0, K40.3, K42.0, K43.0, K80.0, N13.2, I83.2; life-threatening text (estrangul, colangite, sepse, angina em repouso, sincope, retencao urinaria aguda, enterorragia) |
| A2 | 21 days | Any other C*; positive biopsy with benign or uncertain CID; uncertain CID (D37-D48, R91) with suspicious text |
| B | 60 days | Pain >= 7, severe limitation, recent ER visit or hospitalization, functional alarm text (acamado, ulcera de pressao, quedas de repeticao, perda de funcao) |
| C | 180 days | Moderate pain or limitation |
| D | 360 days | Little or no pain or limitation |

Golden rule holds by construction: every C* is in A1/A2, and every "sem urgencia clinica" patient (by the verifier's definition, 237 of them) lands in C/D.

Aging (anti-starvation): passing the tier's max wait raises the time-pressure part of the score; a patient far past it can be promoted one tier, with physician confirmation.

## Layer 2 - Score from 0 to 100 inside each tier

    score = w1*severity + w2*deterioration + w3*time_pressure + w4*predicted_risk + w5*frailty

- Severity: procedure risk (risco_cirurgico 1-5), pain, functional limitation.
- Deterioration: worsening events in 30/90/180 days, days since the last one.
- Time pressure: r = days waited / tier max wait; linear up to 1, convex after (overdue climbs fast).
- Predicted risk: JEV output (../ai/jev.md).
- Frailty: age, ASA, comorbidities.

Ties broken by entry date (FIFO among equals).

Note: 174 of 177 oncologic patients are already past 21 days, so time pressure alone will not separate them. Risk and deterioration have to.

## Readiness (separate from priority)

pronto_para_agendar = pre-anesthetic evaluation done + valid pre-op exams + HbA1c <= 8.5.
Only 136 of 895 are ready today. Readiness filters who can take a slot, it never pushes a patient down.

## Output

- Ordered queue with a receipt per patient (explainability.md).
- fila_priorizada.csv: solicitacao_id, posicao, justificativa. Must pass the official verifier.
- DECISOES.md: what was removed (out/removed.csv) and why.
