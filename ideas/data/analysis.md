# Dataset analysis

What the data looks like and what is broken.
The dataset itself is in dataset/ (see dataset/README.md and dataset/dicionario_dados.md). Numbers below are as of 23/10/2026, the dataset's reference date.

Related: ../prioritization/engine.md (tier rules), ../ai/jev.md (features and label), ../ai/llm.md (text).

## Overview

| File | Rows | What it is |
|---|---|---|
| fila_cirurgica.csv | 941 | One row per request: patient, diagnosis, pain, limitation, wait, manual priority, free text |
| eventos_clinicos.csv | 1,505 | Biopsies, HbA1c, ER visits, hospitalizations, imaging, re-evaluations, calls, no-shows |
| procedimentos.csv | 23 | Specialty, size, surgical risk 1-5, duration, ICU need |
| referencias/swalis.csv | 5 | Urgency classes A1-D, max waits 15, 21, 60, 180, 360 days |

- 177 oncologic by CID (C*), 18 with uncertain CIDs (D37-D48, R91).
- Events linked to 624 requests (median 2 per request).
- Average wait 389 days (median 268). 357 requests waited more than 360 days, past even SWALIS class D.
- 174 of 177 oncologic patients are already past the SWALIS A2 deadline (21 days), median wait 78 days.

## The manual fields are unreliable

- prioridade_regulacao: 90% never revised. 34 oncologic patients are "baixa". 34 non-oncologic patients with no functional limitation are "alta".
- flag_oncologico disagrees with the CID in 44 rows (23 false yes, 21 false no).
- flag_piora_clinica is "nao" for 156 requests that have worsening events.
- flag_diabetico is "nao" for 18 requests that have HbA1c results.

Use these only as the baseline to beat, never as model inputs. Rebuild them from CID, events and text.

## Cleaning (done in build_features.py)

| Problem | Count | What to do |
|---|---|---|
| Duplicate requests (same patient + procedure) | 22 pairs (44 rows) | Keep the earliest entry, move the events and text of the dropped one to it |
| Left the queue (gave up, operated elsewhere or via private insurance) | 24 (13 gave up, 5 elsewhere, 6 only in observacoes) | Remove from the active queue, explain in DECISOES.md |
| Positive biopsy but benign or uncertain CID | 23 (e.g. D05.1, D44.0, R91) | Suspected cancer (suspeita_malignidade), flag the CID for review |
| CID without dot (K409 vs K40.9) | many | Normalize: upper case, no dot |
| Priority spelling (Alta, Média) or empty | 23 + 11 | Normalize, keep empty as unknown |
| Municipality spelling | 62 raw -> 38 normalized | Title case |
| Events pointing to requests not in the queue | 9 | Drop |
| Duplicated events (same content, different id) | 7 | Drop |
| Missing pain / limitation / ASA | 38 / 20 / 26 | Impute + "was missing" flag |
| Vague justification ("Solicito cirurgia.", "Conforme laudo anexo.") | 36 | Low confidence, flag for review |
| Events dated before queue entry | 155 | Keep: they are history (the biopsy that started the request, past ER visits) |

## Readiness numbers

- Pre-anesthetic evaluation pending: 532, expired: 65.
- Pre-op exams not valid: 505.
- Last HbA1c > 8.5: 44.
- Ready to schedule (all three ok): 136 of 895.

## build_features.py

From the ideas/ folder:

    pip install -r data/requirements.txt
    python data/build_features.py               # reads data/dataset, writes to out/

Options: --data (dataset folder), --out, --asof (date, default 2026-10-23), --horizon (label horizon in days, default 90).

- out/features.csv: active queue as of --asof, one row per request, all features (model, rules, readiness, baseline). 895 rows.
- out/removed.csv: requests taken out and why. 46 rows.
- out/train_h90.csv: features as of 90 days earlier + the proxy label, model features only. 734 rows, 158 positives.

Text flags (txt_*, obs_*) are regex stand-ins with a crude "sem X" negation until the LLM extraction is in place.
