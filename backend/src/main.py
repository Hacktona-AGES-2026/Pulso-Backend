"""API do Pulso (rodar de backend/): uvicorn src.main:app --reload

O motor propoe, o medico decide: a fila oficial so muda por POST /mudancas/{id}/decisao.
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from typing import Literal

import os

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from . import db
from .pipeline import consultas, fila as fila_oficial, processamento

app = FastAPI(title="Pulso", description="Priorizacao da fila cirurgica: o motor propoe, o medico decide.")

# Frontend (Vite) roda em outra porta. Origens separadas por virgula em PULSO_CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("PULSO_CORS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def conexao() -> Iterator[psycopg.Connection]:
    with db.conectar() as con:
        yield con


class Decisao(BaseModel):
    decisao: Literal["aprovar", "rejeitar"]
    medico_id: int
    motivo: str | None = None  # obrigatorio para rejeitar


class NovoEvento(BaseModel):
    solicitacao_id: str
    data_evento: date
    tipo_evento: str
    resultado: str
    valor_numerico: float | None = None
    descricao: str = ""
    origem: str = "api"


@app.get("/resumo")
def resumo(con=Depends(conexao)):
    return consultas.resumo(con)


@app.get("/fila")
def listar_fila(modo: Literal["oficial", "recomendada"] = "oficial", fila: str | None = None,
                limite: int = Query(100, le=1000), offset: int = 0, con=Depends(conexao)):
    return consultas.fila(con, modo, fila, limite, offset)


@app.get("/solicitacoes/{solicitacao_id}")
def detalhe(solicitacao_id: str, con=Depends(conexao)):
    s = consultas.solicitacao(con, solicitacao_id)
    if s is None:
        raise HTTPException(404, "solicitacao nao encontrada")
    return s


@app.get("/mudancas")
def caixa_de_pedidos(status: str | None = "pendente", limite: int = Query(100, le=1000), offset: int = 0,
                     con=Depends(conexao)):
    return consultas.mudancas(con, None if status == "todas" else status, limite, offset)


@app.get("/mudancas/{mudanca_id}")
def pedido(mudanca_id: int, con=Depends(conexao)):
    m = consultas.mudanca(con, mudanca_id)
    if m is None:
        raise HTTPException(404, "pedido nao encontrado")
    return m


@app.post("/mudancas/{mudanca_id}/decisao")
def decidir(mudanca_id: int, d: Decisao, con=Depends(conexao)):
    try:
        return fila_oficial.decidir(con, mudanca_id, d.decisao == "aprovar", d.medico_id, d.motivo)
    except fila_oficial.DecisaoInvalida as exc:
        raise HTTPException(409, str(exc))
    except fila_oficial.RegraDeOuroViolada as exc:
        raise HTTPException(409, f"regra de ouro: {exc}. Nada foi alterado.")


@app.post("/eventos", status_code=201)
def novo_evento(ev: NovoEvento, con=Depends(conexao)):
    """Evento novo: entra na fila de processamento e e processado na hora."""
    try:
        evento_id = processamento.registrar_evento(con, ev.model_dump())
    except processamento.EventoInvalido as exc:
        raise HTTPException(422, str(exc))
    return {"evento_id": evento_id, "mudanca": processamento.processar_evento(con, evento_id)}


@app.post("/eventos/processar")
def processar(limite: int = Query(1, ge=1, le=5000), con=Depends(conexao)):
    """Tira os proximos `limite` eventos pendentes da fila de processamento (demo passo a passo)."""
    return processamento.processar_pendentes(con, limite)


@app.get("/pendencias")
def pendencias(con=Depends(conexao)):
    return consultas.pendencias(con)


@app.get("/marcacoes")
def marcacoes(severidade: Literal["alta", "media", "baixa", "informativa"] | None = None, con=Depends(conexao)):
    return consultas.marcacoes(con, severidade)


@app.get("/dados")
def dados(con=Depends(conexao)):
    return consultas.dados(con)


@app.get("/medicos")
def medicos(con=Depends(conexao)):
    return con.execute("""SELECT m.id, m.nome, m.crm, e.nome AS especialidade
                          FROM medico m JOIN especialidade e ON e.id = m.especialidade_id ORDER BY m.id""").fetchall()


@app.get("/export/fila_priorizada.csv", response_class=PlainTextResponse)
def exportar(modo: Literal["oficial", "recomendada"] = "recomendada", con=Depends(conexao)):
    return PlainTextResponse(consultas.csv_fila(con, modo), media_type="text/csv",
                             headers={"Content-Disposition": "attachment; filename=fila_priorizada.csv"})
