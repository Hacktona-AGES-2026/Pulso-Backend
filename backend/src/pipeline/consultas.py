"""Leituras usadas pela CLI e pela API: fila, caixa de pedidos, detalhe, resumo e o CSV."""
from __future__ import annotations

import csv
import io
from pathlib import Path

import psycopg

from .fila import RegraDeOuroViolada, conferir_regra_de_ouro


def fila(con: psycopg.Connection, modo: str = "oficial", grupo: str | None = None,
         limite: int = 100, offset: int = 0) -> list[dict]:
    if modo == "oficial":
        sql = """SELECT fp.posicao_final AS posicao, fp.solicitacao_id, fp.fila, fp.posicao_fila,
                        fp.data_limite_efetiva, fp.posicao_inicial, fp.justificativa,
                        s.cid_principal, s.cid_principal LIKE 'C%%' AS oncologico,
                        m.id AS mudanca_pendente, m.tipo AS mudanca_tipo, m.fila_proposta
                 FROM fila_priorizada fp
                 JOIN solicitacao s ON s.id = fp.solicitacao_id
                 LEFT JOIN solicitacao_mudanca m ON m.solicitacao_id = fp.solicitacao_id AND m.status = 'pendente'
                 WHERE %(grupo)s::text IS NULL OR fp.fila = %(grupo)s
                 ORDER BY fp.posicao_final LIMIT %(limite)s OFFSET %(offset)s"""
    elif modo == "recomendada":
        sql = """SELECT r.posicao, r.solicitacao_id, r.fila, r.data_limite_efetiva, r.justificativa,
                        r.oncologico, fp.posicao_final AS posicao_oficial, fp.fila AS fila_oficial
                 FROM fila_recomendada r
                 LEFT JOIN fila_priorizada fp ON fp.solicitacao_id = r.solicitacao_id
                 WHERE %(grupo)s::text IS NULL OR r.fila = %(grupo)s
                 ORDER BY r.posicao LIMIT %(limite)s OFFSET %(offset)s"""
    else:
        raise ValueError("modo deve ser oficial ou recomendada")
    return con.execute(sql, {"grupo": grupo, "limite": limite, "offset": offset}).fetchall()


def mudancas(con: psycopg.Connection, status: str | None = "pendente", limite: int = 100,
             offset: int = 0) -> list[dict]:
    """Caixa do medico: o destino mais urgente primeiro; saidas por ultimo."""
    return con.execute("""
        SELECT m.id, m.solicitacao_id, m.tipo, m.status, m.fila_atual, m.fila_proposta,
               fp.posicao_final AS posicao_atual, m.posicao_proposta, m.motivo, m.evidencias,
               m.evento_id, m.oncologico, m.criada_em, m.atualizada_em, m.medico_id, m.decidida_em,
               m.motivo_decisao
        FROM solicitacao_mudanca m
        LEFT JOIN fila_grupo g ON g.codigo = m.fila_proposta
        LEFT JOIN fila_priorizada fp ON fp.solicitacao_id = m.solicitacao_id
        WHERE %(status)s::text IS NULL OR m.status = %(status)s
        ORDER BY coalesce(g.ordem, 99), m.posicao_proposta NULLS LAST, m.id
        LIMIT %(limite)s OFFSET %(offset)s""", {"status": status, "limite": limite, "offset": offset}).fetchall()


def mudanca(con: psycopg.Connection, mudanca_id: int) -> dict | None:
    return con.execute("SELECT * FROM solicitacao_mudanca WHERE id = %s", (mudanca_id,)).fetchone()


def solicitacao(con: psycopg.Connection, solicitacao_id: str) -> dict | None:
    s = con.execute("""SELECT s.id, s.paciente_id, s.procedimento_id, p.nome AS procedimento, s.cid_principal,
                              s.cid_descricao, s.intensidade_dor_eva, s.limitacao_funcional,
                              s.justificativa_clinica, s.observacoes, s.data_entrada_fila,
                              s.prioridade_regulacao, s.status, s.duplicata_de, s.motivo_status
                       FROM solicitacao s JOIN procedimento p ON p.id = s.procedimento_id
                       WHERE s.id = %s""", (solicitacao_id,)).fetchone()
    if s is None:
        return None
    s["fila_oficial"] = con.execute("""SELECT posicao_final AS posicao, posicao_inicial, fila, posicao_fila,
                                       data_limite_efetiva, justificativa, marcacoes
                                       FROM fila_priorizada WHERE solicitacao_id = %s""",
                                    (solicitacao_id,)).fetchone()
    s["estado_motor"] = con.execute("SELECT * FROM estado_paciente WHERE solicitacao_id = %s",
                                    (solicitacao_id,)).fetchone()
    s["eventos"] = con.execute("""SELECT id, data_evento, tipo_evento, resultado, valor_numerico, descricao,
                                  origem, processado_em FROM evento_clinico WHERE solicitacao_id = %s
                                  ORDER BY data_evento, id""", (solicitacao_id,)).fetchall()
    s["mudancas"] = con.execute("""SELECT id, tipo, status, fila_atual, fila_proposta, motivo, evento_id,
                                   criada_em, medico_id, decidida_em, motivo_decisao
                                   FROM solicitacao_mudanca WHERE solicitacao_id = %s ORDER BY id""",
                                (solicitacao_id,)).fetchall()
    f = con.execute("SELECT features FROM features_paciente WHERE solicitacao_id = %s", (solicitacao_id,)).fetchone()
    s["features"] = f["features"] if f else None
    return s


def resumo(con: psycopg.Connection) -> dict:
    r = {}
    r["solicitacoes"] = {x["status"]: x["n"] for x in con.execute(
        "SELECT status, count(*) AS n FROM solicitacao GROUP BY 1 ORDER BY 1").fetchall()}
    r["eventos"] = con.execute("""SELECT count(*) FILTER (WHERE processado_em IS NOT NULL) AS processados,
                                         count(*) FILTER (WHERE processado_em IS NULL) AS pendentes
                                  FROM evento_clinico""").fetchone()
    r["eventos"]["quarentena"] = con.execute("SELECT count(*) AS n FROM evento_quarentena").fetchone()["n"]
    tamanhos = con.execute("""
        SELECT g.codigo, g.nome,
               (SELECT count(*) FROM fila_priorizada fp WHERE fp.fila = g.codigo) AS oficial,
               (SELECT count(*) FROM fila_recomendada fr WHERE fr.fila = g.codigo) AS recomendada
        FROM fila_grupo g ORDER BY g.ordem""").fetchall()
    r["filas"] = tamanhos
    r["mudancas"] = {f"{x['tipo']}/{x['status']}": x["n"] for x in con.execute(
        "SELECT tipo, status, count(*) AS n FROM solicitacao_mudanca GROUP BY 1, 2 ORDER BY 1, 2").fetchall()}
    r["regra_de_ouro"] = {}
    for tabela in ("fila_priorizada", "fila_recomendada"):
        try:
            r["regra_de_ouro"][tabela] = conferir_regra_de_ouro(con, tabela)
        except RegraDeOuroViolada as exc:
            r["regra_de_ouro"][tabela] = {"ok": False, "erro": str(exc)}
    return r


def csv_fila(con: psycopg.Connection, modo: str = "recomendada") -> str:
    """O entregavel: solicitacao_id, posicao, justificativa."""
    if modo == "oficial":
        linhas = con.execute("""SELECT solicitacao_id, posicao_final AS posicao, justificativa
                                FROM fila_priorizada ORDER BY posicao_final""").fetchall()
    elif modo == "recomendada":
        linhas = con.execute("SELECT solicitacao_id, posicao, justificativa FROM fila_recomendada ORDER BY posicao").fetchall()
    else:
        raise ValueError("modo deve ser oficial ou recomendada")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["solicitacao_id", "posicao", "justificativa"])
    w.writerows([[x["solicitacao_id"], x["posicao"], x["justificativa"]] for x in linhas])
    return buf.getvalue()


def exportar(con: psycopg.Connection, caminho, modo: str = "recomendada") -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(csv_fila(con, modo), encoding="utf-8")
    return caminho
