# Pulso - Backend

9a Hackatona de Engenharia de Software 2026 (Fin-x, PUCRS, Hospital Sao Lucas), Desafio 1: Priorizacao Inteligente da Fila Cirurgica.

## Status

Core pipeline works end to end on the full dataset (backend/, branch feat/pipeline-fila).
Not built yet: JEV in the pipeline, the monitoring agents, DECISOES.md (see [ideas/ROADMAP.md](ideas/ROADMAP.md)).

## Run (clean machine)

Needs Python 3.10+ and Docker.

    docker compose up -d db
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r backend/requirements.txt
    cd backend
    python -m src.pipeline rodar --recriar     # CSVs -> cleaning -> events -> Postgres -> events one by one (~7 s)
    python -m src.pipeline exportar            # saida/fila_priorizada.csv
    python ../ideas/data/dataset/verificar_fila_priorizada.py saida/fila_priorizada.csv
    uvicorn src.main:app --reload              # API: http://localhost:8000/docs
    python -m pytest                           # uses a separate database, pulso_teste

## Pipeline (backend/src/pipeline)

| Step | Code | What it does |
|---|---|---|
| 1 read | fila_cirurgica/priorizacao/carga.py | the 3 CSVs as they came + sha256 |
| 2 clean | fila_cirurgica/priorizacao/limpeza.py | CID, priority, municipality; 22 duplicates merged into the earliest; 17 exits written in observacoes; 9 orphan events quarantined, 7 repeated dropped |
| 3 events | carga.py | 1,489 valid events, remapped to the master request, enter as pending |
| 4 database | carga.py, db/schema.sql | catalogs, patients, requests, events; initial queue = each active request triaged on its registry only (no events) |
| 5 process | processamento.py | pending events one by one by date: re-triage that patient with every processed event; if the engine wants another group (or the event is an exit) it opens a solicitacao_mudanca for a doctor |

- Official queue (fila_priorizada) changes only when a doctor approves a request: `POST /mudancas/{id}/decisao` or `python -m src.pipeline decidir ID aprovar --medico 1`. Rejecting needs a written reason. Within the same group, tie-breaks and the justification follow the events without a request.
- Every approval renumbers the queue and re-checks the golden rule in one transaction; if it fails nothing changes. A CID C* is never moved down (code + CHECK in the database).
- fila_recomendada (view) is the queue as if every request were approved; `exportar` writes it by default (`--modo oficial` for the official one). It matches the batch engine position by position (test_recomendada_igual_ao_lote_do_motor).
- Engine (groups G1a-G7, signals, negation, classifiers): [fila_cirurgica/README.md](fila_cirurgica/README.md). Database: [db/README.md](db/README.md). build_features.py fills features_paciente (for JEV and the patient detail).

API: `GET /fila?modo=oficial|recomendada`, `GET /mudancas?status=pendente` (doctor's inbox), `POST /mudancas/{id}/decisao`, `POST /eventos` (new event, processed at once), `POST /eventos/processar?limite=N` (step through pending events), `GET /solicitacoes/{id}`, `GET /resumo`, `GET /medicos`, `GET /export/fila_priorizada.csv`.

## Deliverables checklist

- [ ] Public repository with the commit history of the event (by 18:00 Sat 24/10)
- [ ] This README runs the solution on a clean machine
- [ ] DECISOES.md: approach, primary user, why, what was left out on purpose
- [ ] Working solution on the complete dataset
- [ ] fila_priorizada.csv (solicitacao_id, posicao, justificativa), passing `python ideas/data/dataset/verificar_fila_priorizada.py fila_priorizada.csv` (target: 14:00)
- [ ] 5-minute pitch at 19:00
