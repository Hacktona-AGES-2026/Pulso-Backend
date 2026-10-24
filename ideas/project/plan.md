# Plan

## Status

Done:
- Repo with protected main (PR + 1 approval, no force push).
- Dataset analysis (../data/analysis.md).
- data/build_features.py: cleaning + feature table as of any date + training table for JEV.

Not done yet:
- Tier rules + ordering + fila_priorizada.csv + DECISOES.md.
- JEV model.
- LLM text extraction (regex stand-ins today).
- API and frontend.

## Next steps

1. Engine v1: tiers + score with fixed weights -> fila_priorizada.csv with template justifications -> passes the verifier.
2. JEV v1: logistic regression on out/train_h90.csv, backtest vs manual priority, plug into the score.
3. LLM extraction: replace the txt_* / obs_* regex flags with JSON + evidence, same column names.
4. API: queue as of a date, patient receipt, post an event, policies, simulation.
5. Frontend: queue + patient card + replay first, then surgeon and nurse views.
6. Robustness: Monte Carlo ranges, simulation, before/after numbers.
7. Pitch: story, numbers, live demo.

Rule of thumb: always keep a working end-to-end ordering, then improve it.

## Roles

| Role | Owns | Start with |
|---|---|---|
| Data / engine | Tiers, score, ordering, deliverable, DECISOES.md | ../prioritization/engine.md |
| Model | JEV, backtest, Monte Carlo | ../ai/jev.md |
| LLM | Text extraction, explanations, agents for borderline cases | ../ai/llm.md |
| Backend | API | ../tech/architecture.md |
| Frontend | Role views | ../product/frontend.md |
| Pitch | Story, clinical framing, numbers | ../README.md, ../product/vision.md |

## How to work in the repo

- Never push to main. Branch (feat/..., fix/..., docs/...), open a PR, get 1 approval, merge.
- Generated files go to out/ (git-ignored).
- Run the features from the ideas/ folder:

      pip install -r data/requirements.txt
      python data/build_features.py

## Questions

For the team:
- What exactly is JEV: a model someone is building, a fin-x tool, something else? Does it need labels or work from expert priors?

For the organizers / mentors:
- Judging criteria and their weight (technique vs product vs impact).
- Can we use external LLM APIs?
- Any capacity data (rooms, slots)? The dataset has none, so the simulation uses assumed capacity.

Answered by the dataset: no outcomes (we use a proxy label), SWALIS is only a reference, pre-op fields are optional and not evaluated.

## References

- SWALIS (Italy): priority classes with maximum waits (data/dataset/referencias/swalis.csv).
- WCWL priority criteria (Western Canada) and CPAC (New Zealand): point-based clinical priority scores.
- MeNTS score (time-sensitive surgery prioritization).
- TCU audit on elective surgery queues in SUS.
- SISREG / SUS regulation priority colors.

## Name ideas

Chosen: Pulso. Alternatives: Fila Viva, FilaJusta.
