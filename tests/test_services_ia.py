"""Testes do caso de uso de IA (``services.ia``).

O provedor é um mock simples que devolve JSON pré-definido — sem rede, sem
token, sem OpenRouter real. Verifica:

- Interpretação: NL → ``AcaoSugerida`` com operação e parâmetros corretos.
- Parsing resiliente: JSON com markdown fences, campos ausentes, resposta
  inválida.
- Execução: ``executar_acao`` delega corretamente para ``services.tarefas``.
- Guarda-corpo: operação desconhecida levanta erro; ``criar_tarefa`` sem nome
  levanta erro.
"""

from __future__ import annotations

import json

import pytest
import responses
from integrations.openrouter import ProvedorIA
from services.ia import (
    AcaoSugerida,
    InterpretacaoErro,
    executar_acao,
    interpretar_comando,
)

from notion_starter import NotionClient, TaskList
from notion_starter.constants import NOTION_BASE_URL

TOKEN = "ntn_test_token"
DB = "db_tarefas"


# ---------------------------------------------------------------------------
# Mock de provedor
# ---------------------------------------------------------------------------


class ProvedorMock:
    """Provedor que devolve uma resposta fixa, sem rede."""

    def __init__(self, resposta: str) -> None:
        self._resposta = resposta
        self.ultimo_prompt: str | None = None

    def completar(self, prompt: str, *, modelo: str | None = None) -> str:
        self.ultimo_prompt = prompt
        return self._resposta


def _provedor_json(
    operacao: str,
    parametros: dict | None = None,
    descricao: str = "",
) -> ProvedorMock:
    return ProvedorMock(
        json.dumps(
            {
                "operacao": operacao,
                "parametros": parametros or {},
                "descricao": descricao,
            }
        )
    )


def test_provedor_mock_implementa_protocolo():
    assert isinstance(ProvedorMock("x"), ProvedorIA)


# ---------------------------------------------------------------------------
# Helpers de teste
# ---------------------------------------------------------------------------


def _tasklist() -> TaskList:
    return TaskList(NotionClient(token=TOKEN), DB)


def _pagina(id_, nome, status=None, prazo=None):
    props = {"Tarefa": {"type": "title", "title": [{"plain_text": nome}]}}
    if status is not None:
        props["Etapa"] = {"type": "status", "status": {"name": status}}
    if prazo is not None:
        props["Prazo"] = {"type": "date", "date": {"start": prazo}}
    return {"id": id_, "url": f"https://notion.so/{id_}", "properties": props}


# ---------------------------------------------------------------------------
# Interpretar comando
# ---------------------------------------------------------------------------


def test_interpretar_criar_tarefa():
    prov = _provedor_json(
        "criar_tarefa",
        {"nome": "Estudar IA", "prazo": "2026-07-01"},
        "Criar tarefa 'Estudar IA'",
    )
    acao = interpretar_comando("cria tarefa pra estudar IA", provedor=prov)
    assert acao.operacao == "criar_tarefa"
    assert acao.parametros["nome"] == "Estudar IA"
    assert acao.descricao == "Criar tarefa 'Estudar IA'"


def test_interpretar_listar_tarefas():
    prov = _provedor_json("listar_tarefas", {"status": "Entrada"})
    acao = interpretar_comando("mostra as tarefas do inbox", provedor=prov)
    assert acao.operacao == "listar_tarefas"
    assert acao.parametros["status"] == "Entrada"


def test_interpretar_mover_status():
    prov = _provedor_json("mover_status", {"task_id": "t1", "status": "Assim que possível"})
    acao = interpretar_comando("mova t1 pra fazendo", provedor=prov)
    assert acao.operacao == "mover_status"


def test_interpretar_concluir_tarefa():
    prov = _provedor_json("concluir_tarefa", {"task_id": "t1", "status_concluido": "Concluída"})
    acao = interpretar_comando("conclui t1", provedor=prov)
    assert acao.operacao == "concluir_tarefa"


def test_interpretar_operacao_desconhecida():
    prov = _provedor_json("desconhecida", {}, "não entendi")
    acao = interpretar_comando("faça algo aleatório", provedor=prov)
    assert acao.operacao == "desconhecida"


def test_interpretar_json_com_markdown_fences():
    raw = '```json\n{"operacao": "listar_tarefas", "parametros": {}, "descricao": "listar"}\n```'
    prov = ProvedorMock(raw)
    acao = interpretar_comando("lista", provedor=prov)
    assert acao.operacao == "listar_tarefas"


def test_interpretar_resposta_invalida_levanta():
    prov = ProvedorMock("isso não é json nenhum")
    with pytest.raises(InterpretacaoErro, match="não é JSON"):
        interpretar_comando("qualquer coisa", provedor=prov)


def test_interpretar_sem_campo_operacao_levanta():
    prov = ProvedorMock(json.dumps({"parametros": {}}))
    with pytest.raises(InterpretacaoErro, match="operacao"):
        interpretar_comando("qualquer coisa", provedor=prov)


def test_interpretar_envia_prompt_com_instrucoes():
    prov = _provedor_json("listar_tarefas")
    interpretar_comando("lista tarefas", provedor=prov)
    assert "listar_tarefas" in prov.ultimo_prompt
    assert "criar_tarefa" in prov.ultimo_prompt


def test_interpretar_com_modelo_especifico():
    class ProvedorComModelo:
        def completar(self, prompt: str, *, modelo: str | None = None) -> str:
            self.modelo_usado = modelo
            return json.dumps({"operacao": "listar_tarefas", "parametros": {}, "descricao": ""})

    prov = ProvedorComModelo()
    interpretar_comando("lista", provedor=prov, modelo="anthropic/claude-sonnet-4")
    assert prov.modelo_usado == "anthropic/claude-sonnet-4"


# ---------------------------------------------------------------------------
# Executar ação (delega para services.tarefas)
# ---------------------------------------------------------------------------


@responses.activate
def test_executar_listar_tarefas():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json={"results": [_pagina("t1", "A", "Entrada")], "has_more": False},
        status=200,
    )
    acao = AcaoSugerida(operacao="listar_tarefas")
    resultado = executar_acao(acao, tasklist=_tasklist())
    assert isinstance(resultado, list)
    assert resultado[0].nome == "A"


@responses.activate
def test_executar_criar_tarefa():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/pages",
        json=_pagina("novo", "Estudar IA", "Entrada"),
        status=200,
    )
    acao = AcaoSugerida(operacao="criar_tarefa", parametros={"nome": "Estudar IA"})
    resultado = executar_acao(acao, tasklist=_tasklist())
    assert resultado.id == "novo"
    assert resultado.nome == "Estudar IA"


@responses.activate
def test_executar_mover_status():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/pages/t1",
        json=_pagina("t1", "A", "Assim que possível"),
        status=200,
    )
    acao = AcaoSugerida(
        operacao="mover_status",
        parametros={"task_id": "t1", "status": "Assim que possível"},
    )
    resultado = executar_acao(acao, tasklist=_tasklist())
    assert resultado.status == "Assim que possível"


@responses.activate
def test_executar_concluir_tarefa():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/pages/t1",
        json=_pagina("t1", "A", "Concluída"),
        status=200,
    )
    acao = AcaoSugerida(
        operacao="concluir_tarefa",
        parametros={"task_id": "t1", "status_concluido": "Concluída"},
    )
    resultado = executar_acao(acao, tasklist=_tasklist())
    assert resultado.status == "Concluída"


def test_executar_operacao_desconhecida_levanta():
    acao = AcaoSugerida(operacao="explodir_tudo")
    with pytest.raises(ValueError, match="desconhecida"):
        executar_acao(acao, tasklist=_tasklist())


def test_executar_criar_sem_nome_levanta():
    acao = AcaoSugerida(operacao="criar_tarefa", parametros={})
    with pytest.raises(ValueError, match="nome"):
        executar_acao(acao, tasklist=_tasklist())


def test_executar_mover_sem_task_id_levanta():
    acao = AcaoSugerida(operacao="mover_status", parametros={"status": "Assim que possível"})
    with pytest.raises(ValueError, match="task_id"):
        executar_acao(acao, tasklist=_tasklist())


def test_executar_concluir_sem_status_levanta():
    acao = AcaoSugerida(operacao="concluir_tarefa", parametros={"task_id": "t1"})
    with pytest.raises(ValueError, match="status_concluido"):
        executar_acao(acao, tasklist=_tasklist())
