# Pulso - ideas

Working notes, code and data for the fin-x hackathon challenge (Desafio 1: Priorizacao Inteligente da Fila Cirurgica).
Self-contained: copy this folder anywhere.

Unified brief for the team (all of the notes below in one page): pulso-team-brief.html

## Layout

    ideas/
      README.md                  this file: context, challenge rules, pitch
      pulso-team-brief.html      everything in one page, to read or share
      product/
        vision.md                Pulso as a hospital-wide platform: roles, physician confirmation, policies, matching
        frontend.md              one view per hospital role, build priority, demo flow
      prioritization/
        engine.md                tiers (SWALIS hard rules), score, readiness
        explainability.md        the receipt, the justificativa column, confirmations, alerts
        robustness.md            verifier, Monte Carlo, backtest, simulation, sensitivity, equity
      ai/
        jev.md                   first risk score: inputs, what stays out, proxy label, training table
        llm.md                   LLM extraction, explanations, consistency checks, agents
      data/
        analysis.md              what the data looks like, defects, cleaning
        build_features.py        cleaning + feature tables (run it, see below)
        requirements.txt
        dataset/                 the hackathon dataset as provided (CSVs, dictionary, SWALIS, verifier)
      tech/
        architecture.md          event log, engine module, API, stack, data flow
      project/
        plan.md                  status, next steps, roles, repo workflow, open questions, references

## Run

From this folder:

    pip install -r data/requirements.txt
    python data/build_features.py

Writes to out/ (git-ignored):
- out/features.csv: 895 active requests, all features
- out/removed.csv: 46 removed (22 duplicates, 24 exits), with the reason
- out/train_h90.csv: 734 rows, 158 positives, 54 model features (input for JEV)

Check a deliverable with the official verifier:

    python data/dataset/verificar_fila_priorizada.py fila_priorizada.csv

## Context

Sponsor: fin-x, a B2B health-tech company that serves hospitals, private healthcare and SUS. Remote-first.
They process 100k+ surgery orders a month across the whole surgical journey:
pedido -> autorizacao -> agenda -> pre-operatorio -> cirurgia -> remuneracao.
They use AI heavily: models and agents for specialized analysis, rule validation, insights, predictability, efficiency.

The problem (from their slides, citing TCU numbers on surgical queues):
"Hoje a fila mede o tempo, e nao a pessoa."
The queue is ordered by entry date plus a priority assigned by hand on the day the patient is added, and almost never revised.

Dataset (100% synthetic, reference date 23/10/2026): 941 requests, ~1,500 clinical events, 23 procedures, a SWALIS reference table and an official verifier script.

## Rules of the challenge

Fixed:
- The focus is prioritization: who goes first and why.
- The base is the dataset, the whole queue, not a single example.
- Every decision must be explainable.
- The solution must output an order for the queue.
- Golden rule: no patient with a malignant neoplasm (CID starting with C) may be below a patient with no clinical urgency. Use the CID, not the flag.

Free:
- Score engine, decision support, agent, dashboard, process.
- Method: rules, weights, SWALIS, statistics, ML, LLM, consensus...

Deliverables:
- fila_priorizada.csv with solicitacao_id, posicao, justificativa (one row per active request).
- DECISOES.md explaining what was left out and why.
- Demo + pitch (this is what the jury evaluates).

## Pitch

Pulso: a fila cirurgica que mede a pessoa, nao o tempo.

- Conecta hospitais, pacientes e cirurgioes
- Prioriza por condicao clinica, nao por data de entrada
- Se atualiza a partir de eventos clinicos, tempo de espera e risco
- Explica cada posicao na fila
- Valida toda mudanca com um medico responsavel
- Se adapta a equipe, recursos e complexidade de cada hospital
- Combina paciente, cirurgia, sala e equipe
- Usa IA (machine learning + agentes) para apoiar a decisao medica, sem substitui-la
