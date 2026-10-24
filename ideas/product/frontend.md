# Frontend

One view per hospital role, all reading the same queue. Each person opens Pulso and sees what they need to do today.
Related: vision.md (the roles), ../prioritization/explainability.md (the receipt), ../tech/architecture.md (the API the views read from).

## Shared pieces

- Patient card: receipt (tier, score parts, reason for upgrades), event timeline, readiness checklist,
  Monte Carlo range ("8-14 in 95% of scenarios"), LLM explanation, history of confirmations and overrides.
- Tier badge (A1, A2, B, C, D) and readiness badge (ready / not ready + why) everywhere a patient appears.
- Movement arrows (moved up / down since the last update) and alert badges.
- Date selector: every view can be shown "as of" a date (the queue is rebuilt from events).

## Views

### 1. Regulation - the queue

The central view, for the regulation team.
- Whole queue in order: position, patient, procedure, tier, score, days waited, % of max wait used, ready or not.
- Filters: tier, specialty, procedure, overdue, ready to schedule, suspected malignancy, alerts.
- Before/after toggle: current method (entry date + manual priority) vs Pulso.

### 2. Surgeon - my patients

- Only the surgeon's patients.
- Pending confirmations: "Pulso proposes moving Joao from C to B (ER visit 12/10). Confirm / reject + reason."
- Alerts when one of their patients gets worse.
- Structured assessment form when adding a new patient (replaces the manual alta/media/baixa).

### 3. Nurse navigator - today's contacts

- To-do list: patients with red flags, no contact in X days, unreachable (obs_sem_contato), transport needs (TFD).
- Log the contact result (answered, reports worsening, reports improvement, gave up, operated elsewhere) -> becomes an event -> queue updates.

### 4. Scheduling - fill a slot

- Pick a slot (room, date, duration, ICU available or not).
- Ranked candidates: highest priority first, only ready patients, procedure duration fits, ICU need matches.
- For each candidate, why it fits or not ("not ready: pre-anesthetic pending").

### 5. Pre-op - high priority, not ready

- Patients in A1/A2/B who are not ready: pre-anesthetic pending/expired, exams not valid, HbA1c > 8.5.
- Sorted by priority, so the pre-op team unblocks the most urgent first.

### 6. Patient - WhatsApp check-in (mock)

- Chat-style screen: "Ola Maria, como voce esta? Algo mudou desde o ultimo contato?"
- Answers become events (reports worsening -> alert to nurse and surgeon).
- Shows status and expected time window, not the exact position.

### 7. Clinical board - policies

- Current policy version, weights and tier rules.
- Weight sliders: queue reorders live, shows how many patients moved.
- Shadow mode: "with v1.2, these 14 patients would move" before activating.
- Equity report (positions by age group, sex, municipality) and override audit.

### 8. Replay - time machine

- Time slider over the dataset's dates.
- Events arrive, the queue reorders, alerts fire.
- The main demo moment: the queue reacts to the person.

### 9. Results - before / after

- Big numbers from the simulation: patients past max wait, worsening while waiting, wait of A1/A2, wait of C/D.
- Verifier indicators: median position of oncologic patients, recent ER/hospitalization in the first half.

## What to build first (hackathon scope)

Must: 1 (queue + patient card), 8 (replay), 2 (surgeon confirmations), 3 (nurse to-do list).
Should: 4 (scheduling), 7 (weights + shadow mode), 9 (before/after).
Could: 5 (pre-op), 6 (WhatsApp mock).

## Demo flow (pitch)

1. Regulation view with the current method: one patient stuck low despite getting worse.
2. Replay: move the slider, an ER visit arrives, Pulso proposes moving the patient up.
3. Surgeon view: the surgeon confirms, with a reason.
4. Patient card: open the receipt, ask "why is A ahead of B?".
5. Nurse view: the patient shows up on today's contacts; WhatsApp check-in reports worsening.
6. Scheduling: a slot opens, the top ready candidates appear.
7. Clinical board: move a weight slider, show the robustness range and shadow mode.
8. End on the before/after numbers.

## Tech

- React (Next.js or Vite) + a component library for speed; FastAPI backend serving the engine.
- Streamlit multipage is the fallback if frontend time is short (fewer role views, same engine).
- Pages read from the API only; no prioritization logic in the frontend.
