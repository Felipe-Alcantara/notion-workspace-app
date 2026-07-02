"""Testes dos casos de uso de tarefas (``services.tarefas``).

A ``TaskList`` é injetada e o HTTP do Notion é mockado com ``responses`` — sem
token nem rede real. Verifica que cada caso de uso delega corretamente à
``TaskList`` e devolve a tarefa normalizada.
"""

from __future__ import annotations

import json

import responses
from services import tarefas as svc

from notion_starter import NotionClient, TaskList
from notion_starter.constants import NOTION_BASE_URL

TOKEN = "ntn_test_token"
DB = "db_tarefas"


def _tasklist() -> TaskList:
    return TaskList(NotionClient(token=TOKEN), DB)


def _pagina(id_, nome, status=None, prazo=None, duracao=None, areas=None):
    props = {"Tarefa": {"type": "title", "title": [{"plain_text": nome}]}}
    if status is not None:
        props["Etapa"] = {"type": "status", "status": {"name": status}}
    if prazo is not None:
        props["Prazo"] = {"type": "date", "date": {"start": prazo}}
    if duracao is not None:
        props["Esforço"] = {"type": "status", "status": {"name": duracao}}
    if areas is not None:
        props["Áreas da vida"] = {
            "type": "relation",
            "relation": [{"id": area_id} for area_id in areas],
        }
    return {"id": id_, "url": f"https://notion.so/{id_}", "properties": props}


@responses.activate
def test_listar_tarefas_delega_para_tasklist():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json={"results": [_pagina("t1", "A", "Entrada")], "has_more": False},
        status=200,
    )
    tarefas = svc.listar_tarefas(tasklist=_tasklist())
    assert [t.nome for t in tarefas] == ["A"]


@responses.activate
def test_listar_tarefas_filtra_por_status():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json={"results": [], "has_more": False},
        status=200,
    )
    svc.listar_tarefas(status="Entrada", tasklist=_tasklist())
    corpo = json.loads(responses.calls[0].request.body)
    assert corpo["filter"] == {"property": "Etapa", "status": {"equals": "Entrada"}}


@responses.activate
def test_listar_tarefas_repassa_filtros_amplos():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json={"results": [], "has_more": False},
        status=200,
    )
    svc.listar_tarefas(
        status="Entrada",
        duracao="Dias",
        areas=["a1"],
        tasklist=_tasklist(),
    )
    corpo = json.loads(responses.calls[0].request.body)
    assert corpo["filter"] == {
        "and": [
            {"property": "Etapa", "status": {"equals": "Entrada"}},
            {"property": "Esforço", "status": {"equals": "Dias"}},
            {"property": "Áreas da vida", "relation": {"contains": "a1"}},
        ]
    }


@responses.activate
def test_criar_tarefa_devolve_tarefa_criada():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/pages",
        json=_pagina("novo", "Nova", "Entrada", duracao="Dias", areas=["a1"]),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/databases/{DB}",
        json={
            "properties": {
                "Áreas da vida": {
                    "type": "relation",
                    "relation": {"database_id": "db_areas"},
                }
            }
        },
        status=200,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/db_areas/query",
        json={
            "results": [
                {
                    "id": "a1",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Estudos"}]}
                    },
                }
            ],
            "has_more": False,
        },
        status=200,
    )
    tarefa = svc.criar_tarefa(
        "Nova",
        status="Entrada",
        duracao="Dias",
        areas=["a1"],
        tasklist=_tasklist(),
    )
    assert tarefa.id == "novo"
    assert tarefa.nome == "Nova"
    assert tarefa.duracao == "Dias"
    assert tarefa.areas == ["a1"]
    assert tarefa.areas_nomes == ["Estudos"]


@responses.activate
def test_editar_tarefa_delega_campos_amplos():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/pages/t1",
        json=_pagina("t1", "Renomeada", "Assim que possível", duracao="Poucas horas"),
        status=200,
    )
    tarefa = svc.editar_tarefa(
        "t1",
        nome="Renomeada",
        status="Assim que possível",
        duracao="Poucas horas",
        tasklist=_tasklist(),
    )
    corpo = json.loads(responses.calls[0].request.body)
    assert corpo["properties"]["Tarefa"]["title"][0]["text"]["content"] == "Renomeada"
    assert corpo["properties"]["Esforço"]["status"]["name"] == "Poucas horas"
    assert tarefa.nome == "Renomeada"


@responses.activate
def test_mover_status_faz_patch():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/pages/t1",
        json=_pagina("t1", "A", "Assim que possível"),
        status=200,
    )
    tarefa = svc.mover_status("t1", "Assim que possível", tasklist=_tasklist())
    assert tarefa.status == "Assim que possível"


@responses.activate
def test_concluir_tarefa_usa_status_informado():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/pages/t1",
        json=_pagina("t1", "A", "Concluída"),
        status=200,
    )
    tarefa = svc.concluir_tarefa("t1", "Concluída", tasklist=_tasklist())
    assert tarefa.status == "Concluída"


@responses.activate
def test_listar_opcoes_delega_para_tasklist():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/databases/{DB}",
        json={
            "properties": {
                "Etapa": {
                    "type": "status",
                    "status": {"options": [{"name": "Entrada"}]},
                },
                "Esforço": {
                    "type": "status",
                    "status": {"options": [{"name": "Dias"}]},
                },
                "Áreas da vida": {
                    "type": "relation",
                    "relation": {"database_id": "db_areas"},
                },
            },
        },
        status=200,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/db_areas/query",
        json={
            "results": [
                {
                    "id": "a1",
                    "properties": {
                        "Tarefa": {
                            "type": "title",
                            "title": [{"plain_text": "Estudos"}],
                        }
                    },
                }
            ],
            "has_more": False,
        },
        status=200,
    )
    assert svc.listar_opcoes(tasklist=_tasklist()) == {
        "status": ["Entrada"],
        "duracao": ["Dias"],
        "areas": [{"id": "a1", "nome": "Estudos"}],
    }
