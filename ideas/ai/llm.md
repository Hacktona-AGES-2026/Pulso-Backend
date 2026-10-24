# LLMs and agents

The LLM extracts and explains. The engine decides, deterministically.
Why: an LLM is not deterministic and is hard to audit. Keeping it on the extraction and explanation side gives the AI fin-x likes without losing explainability.

## 1. Justification text -> structured signals

- Input: justificativa_clinica (about 104 characters on average, 36 are vague like "Solicito cirurgia.").
- Output: JSON per request with alarm categories and the quoted evidence.
- Categories (same names as the regex stand-ins in ../data/build_features.py, so swapping in the LLM changes nothing downstream):
  txt_obstrucao, txt_infeccao, txt_sangramento, txt_progressao_tumoral, txt_cardiorresp, txt_funcional, txt_suspeita_malignidade, txt_piora, txt_vaga.
- Why the LLM: the verifier's regex catches 124 alarm mentions but cannot handle negation ("sem sinais de encarceramento") or paraphrase.

## 2. observacoes -> signals

- Exits (gave up, operated elsewhere, with date when given).
- Reported worsening ("PCT REFERE PIORA. SOLICITA AGILIZAR.").
- The 12 "Familiar informa internacao recente na UPA" notes: worsening with no event registered.
- Unreachable patients (24), transport / TFD needs (59).
- Stand-in columns today: obs_piora, obs_internacao, obs_sem_contato, obs_transporte.

## 3. Consistency checks

- Manual flags vs CID and events (44 oncologic flag mismatches, 156 missed worsening).
- Positive biopsy with benign or uncertain CID (23 cases): suggest a CID review.
- Vague justifications: flag for the surgeon to complete.

## 4. Explanations

- Plain-language version of a receipt, for doctors or for patients.
- "Why is A ahead of B?" by comparing two receipts.
- Not used for the deliverable's justificativa column (that comes from a deterministic template, see ../prioritization/explainability.md).

## 5. Agents simulating the medical team

- Roles: surgeon, anesthesiologist, regulator.
- Only on borderline cases: near a tier boundary, or with a wide Monte Carlo range.
- They produce a recommendation and reasons; a physician confirms (../product/vision.md).

## Guardrails

- Store LLM output as structured fields with the quoted evidence, never free-form decisions.
- Cache results so the order is reproducible.
- The data is synthetic, so calling an external API is fine for the hackathon (confirm with the organizers).
