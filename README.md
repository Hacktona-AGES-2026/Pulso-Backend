# Pulso - Backend

9a Hackatona de Engenharia de Software 2026 (Fin-x, PUCRS, Hospital Sao Lucas), Desafio 1: Priorizacao Inteligente da Fila Cirurgica.

## Status

Core pipeline works end to end on the full dataset (backend/, branch feat/pipeline-fila).
Not built yet: JEV in the pipeline, the monitoring agents, DECISOES.md (see [ideas/ROADMAP.md](ideas/ROADMAP.md)).

## Run (clean machine)

Needs Docker only.

    docker compose up -d --build

The first start takes about a minute: the `api` container waits for Postgres, then runs `python -m src.pipeline rodar --se-vazio` (CSVs -> cleaning -> events -> Postgres -> events one by one) and starts the API. On later starts the database is already loaded and the step is skipped.

- API: http://localhost:8000/docs (CORS allows the frontend on http://localhost:5173 and :5174)
- Follow the seeding: `docker compose logs -f api`
- Reload the data from scratch (wipes the database, including decisions made): `docker compose exec api python -m src.pipeline rodar --recriar`
- Reset everything, volume included: `docker compose down -v`
- Frontend: see [../Pulso-Frontend](../Pulso-Frontend). Doctor login uses a CRM from `GET /medicos` (e.g. `CRM-RS 900001`) and any password with 4+ characters.

Without Docker for the API (needs Python 3.10+; Postgres still comes from Docker):

    docker compose up -d db
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r backend/requirements.txt
    cd backend
    python -m src.pipeline rodar --recriar     # CSVs -> cleaning -> events -> Postgres -> events one by one (~7 s)
    # demo instead: load, then process events only until the doctor's inbox has 3 requests;
    # the rest stay pending for the "process next event" button (POST /eventos/processar)
    python -m src.pipeline carregar --recriar --ate-pedidos 3
    python -m src.pipeline exportar            # saida/fila_priorizada.csv
    python ../ideas/data/dataset/verificar_fila_priorizada.py saida/fila_priorizada.csv
    uvicorn src.main:app --reload              # API: http://localhost:8000/docs
    python -m pytest                           # uses a separate database, pulso_teste

If the local `uvicorn` and the `api` container both run, they share port 8000 (one on IPv4, one on IPv6) and requests may hit either; run only one.

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

### Plain-language explanations (LLM, optional)

backend/src/pipeline/explicacao.py: an LLM rewrites the engine's facts (group, deadline, wait, evidence with dates and quotes, alerts, pending items, request waiting for the doctor) into 2-3 sentences. It never changes the queue.
After every answer a deterministic check rejects any number or date, group code or name, or oncology term that is not in the facts, and "no pending items/alerts" when the facts list some; one retry with the reason, then the template text stands. Texts are cached in `explicacao` by a hash of the facts (same facts, same text; a new event regenerates it).

    OLLAMA_NUM_PARALLEL=4 ollama serve && ollama pull gemma4:e4b   # local (default); or PULSO_LLM_PROVIDER=groq + GROQ_API_KEY
    python -m src.pipeline explicar mudancas --limite 0    # whole doctor's inbox (128 requests, ~8 min)
    python -m src.pipeline explicar fila --limite 50       # top of the queue (--limite 0 = all 897, ~1 h)

Model (local, at most 4B, same 16-text sample, M3 Pro): gemma4:e4b (default, 4B effective) about 4 s per text with 4 in parallel and the fewest mistakes;
gemma4:e2b about 2 s per text, more mistakes, most of them caught by the check and fixed on the retry (`PULSO_LLM_MODEL=gemma4:e2b`).
llama3.2, qwen3:4b and gemma3:4b passed the check but wrote wrong things it cannot see (position read as a group, "no pending items" when there were, CID attached to the wrong diagnosis).
    python -m src.pipeline exportar --explicacao            # justificativa = LLM text where generated

Generated texts are versioned in db/explicacoes.jsonl (input facts + text + model): `rodar --recriar` imports them, so a clone or a reload needs no LLM for this dataset.
`explicar` updates the file; texts made on demand through the API are saved with `python -m src.pipeline salvar-explicacoes`.

### Máquina do Tempo (impacto medido)

`fila_cirurgica/maquina_tempo/` (módulo irmão de `priorizacao`): rebobina o log de eventos e reavalia cada paciente a cada novo evento. Mede quantos pacientes o motor teria promovido de fila durante a espera e o gap com a prioridade manual. Determinístico, sem vazamento de futuro, não toca na fila oficial.

    cd fila_cirurgica && python -m maquina_tempo            # manchete + top casos
    python -m maquina_tempo --caso SOL-2025-00478           # linha do tempo de 1 paciente

API: `GET /maquina-tempo` serve a mesma manchete (em cache; o dataset é estático).

## Deliverables checklist

- [ ] Public repository with the commit history of the event (by 18:00 Sat 24/10)
- [ ] This README runs the solution on a clean machine
- [ ] DECISOES.md: approach, primary user, why, what was left out on purpose
- [ ] Working solution on the complete dataset
- [ ] fila_priorizada.csv (solicitacao_id, posicao, justificativa), passing `python ideas/data/dataset/verificar_fila_priorizada.py fila_priorizada.csv` (target: 14:00)
- [ ] 5-minute pitch at 19:00
