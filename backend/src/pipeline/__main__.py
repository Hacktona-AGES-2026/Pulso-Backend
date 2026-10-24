"""CLI do pipeline (rodar de backend/).

  python -m src.pipeline rodar --recriar          passos 1-5: CSVs -> limpeza -> eventos -> banco -> processamento
  python -m src.pipeline carregar --recriar       so 1-4 (eventos ficam pendentes)
  python -m src.pipeline processar [--limite N]   tira N eventos da fila de processamento
  python -m src.pipeline mudancas [--status pendente]
  python -m src.pipeline decidir ID aprovar|rejeitar --medico 1 [--motivo "..."]
  python -m src.pipeline aprovar-todas --medico 1 (demo/teste: fila oficial = recomendada)
  python -m src.pipeline varrer [--data AAAA-MM-DD]
  python -m src.pipeline exportar [--modo recomendada|oficial] [--saida saida/fila_priorizada.csv]
  python -m src.pipeline resumo
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from .. import db
from . import carga, consultas, fila, processamento


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m src.pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("rodar", "carregar"):
        p = sub.add_parser(nome)
        p.add_argument("--recriar", action="store_true", help="apaga o banco e carrega de novo")
        p.add_argument("--dataset")
        p.add_argument("--data-referencia")
    p = sub.add_parser("processar")
    p.add_argument("--limite", type=int)
    p = sub.add_parser("mudancas")
    p.add_argument("--status", default="pendente")
    p.add_argument("--limite", type=int, default=20)
    p = sub.add_parser("decidir")
    p.add_argument("id", type=int)
    p.add_argument("decisao", choices=["aprovar", "rejeitar"])
    p.add_argument("--medico", type=int, required=True)
    p.add_argument("--motivo")
    p = sub.add_parser("aprovar-todas")
    p.add_argument("--medico", type=int, required=True)
    p = sub.add_parser("varrer")
    p.add_argument("--data")
    p = sub.add_parser("exportar")
    p.add_argument("--modo", default="recomendada", choices=["recomendada", "oficial"])
    p.add_argument("--saida", default="saida/fila_priorizada.csv")
    sub.add_parser("resumo")
    a = ap.parse_args(argv)

    with db.conectar() as con:
        t0 = time.time()
        if a.cmd in ("rodar", "carregar"):
            from pathlib import Path
            r = carga.carregar(con, Path(a.dataset) if a.dataset else None, a.data_referencia, a.recriar)
            _imprimir("carga (passos 1-4)", r)
            if a.cmd == "rodar":
                _imprimir("processamento (passo 5)", processamento.processar_pendentes(con))
                _imprimir_resumo(consultas.resumo(con))
        elif a.cmd == "processar":
            _imprimir("processamento", processamento.processar_pendentes(con, a.limite))
        elif a.cmd == "mudancas":
            for m in consultas.mudancas(con, None if a.status == "todas" else a.status, a.limite):
                print(f"#{m['id']:<5} {m['status']:<10} {m['tipo']:<6} {m['solicitacao_id']}  "
                      f"{m['fila_atual']}@{m['posicao_atual']} -> {m['fila_proposta'] or 'fora'}@{m['posicao_proposta'] or '-'}"
                      f"  {m['motivo'][:110]}")
        elif a.cmd == "decidir":
            _imprimir("decisao", fila.decidir(con, a.id, a.decisao == "aprovar", a.medico, a.motivo))
        elif a.cmd == "aprovar-todas":
            n = 0
            while pend := consultas.mudancas(con, "pendente", limite=1):
                fila.decidir(con, pend[0]["id"], True, a.medico, "aprovacao em lote (demo)")
                n += 1
            print(f"{n} pedidos aprovados")
        elif a.cmd == "varrer":
            _imprimir("varredura", processamento.varrer(con, a.data))
        elif a.cmd == "exportar":
            print(consultas.exportar(con, a.saida, a.modo))
        elif a.cmd == "resumo":
            _imprimir_resumo(consultas.resumo(con))
        print(f"({time.time() - t0:.1f} s)", file=sys.stderr)
    return 0


def _imprimir(titulo, d) -> None:
    print(f"== {titulo}")
    print(json.dumps(d, ensure_ascii=False, indent=2, default=str))


def _imprimir_resumo(r) -> None:
    print("== resumo")
    print(f"solicitacoes: {r['solicitacoes']}")
    print(f"eventos: {r['eventos']}")
    print(f"{'fila':5} {'nome':28} {'oficial':>8} {'recomendada':>12}")
    for f in r["filas"]:
        print(f"{f['codigo']:5} {f['nome']:28} {f['oficial']:>8} {f['recomendada']:>12}")
    print(f"pedidos de mudanca: {r['mudancas']}")
    for t, g in r["regra_de_ouro"].items():
        print(f"regra de ouro {t}: {'ok' if g.get('ok') else 'VIOLADA ' + g.get('erro', '')}")


if __name__ == "__main__":
    sys.exit(main())
