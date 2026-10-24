# Product vision: Pulso for the whole hospital

The algorithm is one part. The product is the whole hospital working from the same living queue.
Instead of one dashboard for one manager, every role feeds signals in and gets its own to-do list out.

Related: frontend.md (the views), ../tech/architecture.md (event log, API), ../prioritization/engine.md (the ordering).

## The queue is built from events

The system stores events: request created, pre-op exam done, ER visit, patient reported more pain, authorization approved, slot cancelled.
The ordered queue is computed from those events by the current prioritization policy.

Why this matters:
- Full audit trail: "why was Maria 12th on Oct 3?" -> rebuild the queue as it was that day, with the policy in force.
- Backtests for free: replaying past events is the backtest.
- Any source can feed it: nurse, patient, ER system, scheduler.

The dataset already has this shape (dated events per request), and data/build_features.py builds the features "as of" any date.

## Who uses it

| Role | Adds | Gets |
|---|---|---|
| Surgeon | Adds the patient with a short structured assessment | Alerts when their patients get worse; tier changes to confirm |
| Nurse navigator | Regular check-ins with waiting patients | Daily to-do list: who to contact, who has red flags |
| Patient | WhatsApp check-in: "has anything changed?" | Status and expected time window (not the exact position) |
| ER / outpatient | ER visit of a waiting patient, logged automatically | (nothing to do) |
| Pre-op team | Exams, pre-anesthetic evaluation, risk assessment | Patients high in the queue but not ready |
| Surgery scheduling | Free slots, cancellations, room and surgeon capacity | "Slot open tomorrow 8:00: 3 ready candidates, in order" |
| OPME / authorization | Implant availability, insurer authorization status | Pending items sorted by patient priority |
| Clinical board | Approves prioritization rules and weights | Overrides audit, equity report, KPIs |
| Regional regulator (SUS) | (network level) | Combined queue across hospitals, possible transfers |

## Physician confirmation

The engine proposes, a responsible physician confirms.
- Tier changes (up or down) wait for confirmation by the patient's surgeon or the regulation physician.
- Small reorders inside a tier apply automatically (they come from the approved policy).
- Every confirmation and override is logged with who, when and why.

## What makes it real software

1. Policies as versions: weights and tier rules are a document the clinical board approves (v1.0, v1.1...).
   A new policy runs in shadow mode first ("with v1.2, these 14 patients would move"). Every ordering records which version produced it.
2. Integration through adapters: hospital systems in Brazil (Tasy, MV) talk HL7/FHIR; insurer authorizations use TISS (ANS); procedures and diagnoses use TUSS and CID-10.
   In the hackathon these are mocks, but the adapter layer exists.
3. Multi-tenant: network -> hospital -> specialty -> queue. Matches fin-x selling to many hospitals.
4. LGPD and access control: each role sees only what it needs, every access and override is logged, patients consent before being contacted.
5. Safe failure: the engine is deterministic; if it goes down everyone works from the last snapshot.

## Matching (patient, surgery, room, team)

Scheduling a free slot is a match, not just "next in line":
- Candidates: highest priority first, filtered by readiness (pre-op done, exams valid, HbA1c controlled).
- Fit: procedure duration (duracao_media_min) fits the slot, ICU bed available when necessita_uti = sim, surgeon/specialty available.
- The scheduler sees the top candidates and why each one fits or not.

The dataset has duration and ICU need per procedure but no capacity data, so capacity in the demo is assumed and must be said so.

## What to build in the hackathon

One complete path through the product:
- Replay the dataset as a live stream: time slider, events arrive, queue reorders, alerts fire.
- 3 role views instead of 1 dashboard: nurse navigator, scheduling, surgeon.
- Simulated WhatsApp check-in: patient reports worsening -> event -> patient moves up -> nurse and surgeon get an alert.
- Policy versioning + shadow mode on one screen.
- Audit: rebuild the queue as of date X.

Roadmap for the pitch slide: real HIS integrations, multi-tenant, regional regulator view.
