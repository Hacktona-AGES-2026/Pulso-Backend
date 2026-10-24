# JEV - the first risk score

Probability that a waiting patient gets worse soon. It is one part of the score (../prioritization/engine.md), never the whole order.
Open question: what exactly JEV is (a model one of us builds, a fin-x tool, something else) and whether it needs labels or works from expert priors.

## Input

One row per request, computed as of a date, so we can backtest without leaking the future.
The exact list is MODEL_FEATURES in ../data/build_features.py (54 features).

- Patient: age, sex, ASA (+ missing), comorbidity count, key comorbidities (DM2, ICC, cardiopatia isquemica, DPOC, DRC, anticoagulacao, FA, obesidade, tabagismo), diabetic (rebuilt).
- Diagnosis: oncologic by CID, uncertain CID, urgent CID, positive biopsy.
- Procedure: risco_cirurgico, porte, necessita_uti.
- Clinical status: pain (EVA), functional limitation 0-3 (+ missing flags).
- Events: worsening in 30/90/180 days, days since last worsening, ER visits, hospitalizations, days hospitalized, imaging progression, re-evaluation worse/better, reported worsening/improvement, missed appointments (180 days), last HbA1c and trend.
- Time: days in queue, days since last priority review.
- Text flags (txt_*), regex today, LLM later (../ai/llm.md). Booleans, never raw text.

## Kept out

- Name and ids.
- Municipality and distance (equity: logistics only).
- Manual priority and manual flags (noisy, human bias, baseline only).
- Pre-op fields (readiness, not severity).

## Label

There are no outcomes in the dataset. Proxy label:
features as of (reference date - horizon), label = worsening event (ER visit, hospitalization, imaging progression, re-evaluation worse, reported worsening) within the horizon.

| Horizon | Patients at risk | Positives |
|---|---|---|
| 60 days | 834 | 145 (17%) |
| 90 days | 768 | 158 (21%) |
| 120 days | 707 | 156 (22%) |
| 180 days | 606 | 136 (22%) |

After cleaning (duplicates and exits removed), out/train_h90.csv has 734 rows, 158 positives (22%), no empty values.

Signal check: label rate 72% with a worsening in the previous 90 days vs 18% without; 52% for oncologic vs 17%.
Caveat: worsening events cluster near the reference date in this synthetic data (180-day horizon: only 3 positives had an earlier worsening), so the model leans on static features.

## Model

- Start with a regularized logistic regression: about 20 features is what 158 positives support, and coefficients are auditable.
- Bayesian priors from clinical knowledge help with this little data.
- Validate with the backtest (../prioritization/robustness.md): precision@k and AUC against the manual priority.
- Output a probability per patient; the engine turns it into the predicted_risk part of the score.
