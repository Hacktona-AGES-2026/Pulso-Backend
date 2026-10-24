# Pulso - Backend

9a Hackatona de Engenharia de Software 2026 (Fin-x, PUCRS, Hospital Sao Lucas), Desafio 1: Priorizacao Inteligente da Fila Cirurgica.

## Status

Planning and data preparation. Notes, the dataset and the feature script live in [ideas/](ideas/README.md).
The priority queue engine, JEV, the agents, the API, fila_priorizada.csv and DECISOES.md are not built yet (see [ideas/ROADMAP.md](ideas/ROADMAP.md)).

## Run what exists (clean machine)

Needs Python 3.10+.

    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r ideas/data/requirements.txt
    python ideas/data/build_features.py --out ideas/out

Writes ideas/out/features.csv (895 active requests), ideas/out/removed.csv (46 removed) and ideas/out/train_h90.csv.

## Deliverables checklist

- [ ] Public repository with the commit history of the event (by 18:00 Sat 24/10)
- [ ] This README runs the solution on a clean machine
- [ ] DECISOES.md: approach, primary user, why, what was left out on purpose
- [ ] Working solution on the complete dataset
- [ ] fila_priorizada.csv (solicitacao_id, posicao, justificativa), passing `python ideas/data/dataset/verificar_fila_priorizada.py fila_priorizada.csv` (target: 14:00)
- [ ] 5-minute pitch at 19:00
