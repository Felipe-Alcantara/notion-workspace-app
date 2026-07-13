"""Testes dos casos de uso de conteúdo (``services.conteudo``).

O :class:`NotionClient` é injetado e o HTTP do Notion é mockado com
``responses`` — sem token nem rede real. Verifica que cada caso de uso delega à
camada de conteúdo e devolve o resultado normalizado, incluindo o fluxo
destrutivo (``excluir_bloco``).
"""

from __future__ import annotations

import json

import pytest
import responses
from notion_starter import NotionClient
from notion_starter.constants import NOTION_BASE_URL
from services import conteudo as svc

TOKEN = "ntn_test_token"


def _cliente() -> NotionClient:
    return NotionClient(token=TOKEN, max_retries=0)


@responses.activate
def test_ler_conteudo_devolve_markdown():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/blocks/page1/children",
        json={
            "results": [
                {"type": "heading_1", "heading_1": {"rich_text": [{"plain_text": "T"}]}},
                {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "oi"}]}},
            ],
            "has_more": False,
        },
        status=200,
    )
    assert svc.ler_conteudo("page1", cliente=_cliente()) == "# T\n\noi"


@responses.activate
def test_escrever_conteudo_anexa_e_conta_blocos():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/blocks/page1/children",
        json={"results": []},
        status=200,
    )
    total = svc.escrever_conteudo("page1", "linha um\nlinha dois", cliente=_cliente())
    assert total == 2
    corpo = json.loads(responses.calls[0].request.body)
    assert len(corpo["children"]) == 2


@responses.activate
def test_escrever_conteudo_fatia_em_lotes_de_100():
    def _eco(request):
        filhos = json.loads(request.body)["children"]
        return (200, {}, json.dumps({"results": filhos}))

    responses.add_callback(
        responses.PATCH,
        f"{NOTION_BASE_URL}/blocks/page1/children",
        callback=_eco,
        content_type="application/json",
    )
    markdown = "\n\n".join(f"linha {i}" for i in range(250))
    total = svc.escrever_conteudo("page1", markdown, cliente=_cliente())
    assert total == 250
    tamanhos = [len(json.loads(c.request.body)["children"]) for c in responses.calls]
    assert tamanhos == [100, 100, 50]


def test_escrever_conteudo_vazio_levanta():
    with pytest.raises(ValueError):
        svc.escrever_conteudo("page1", "   ", cliente=_cliente())


@responses.activate
def test_editar_bloco_envia_so_o_primeiro_bloco():
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/blocks/b1",
        json={"id": "b1"},
        status=200,
    )
    svc.editar_bloco("b1", "## Novo título", cliente=_cliente())
    corpo = json.loads(responses.calls[0].request.body)
    assert "heading_2" in corpo


@responses.activate
def test_excluir_bloco_delega_delete():
    responses.add(
        responses.DELETE,
        f"{NOTION_BASE_URL}/blocks/b1",
        json={"id": "b1", "archived": True},
        status=200,
    )
    resultado = svc.excluir_bloco("b1", cliente=_cliente())
    assert resultado["archived"] is True
    assert responses.calls[0].request.method == "DELETE"


@responses.activate
def test_buscar_normaliza_paginas_e_databases():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/search",
        json={
            "results": [
                {
                    "object": "page",
                    "id": "p1",
                    "url": "https://notion.so/p1",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Nota"}]}
                    },
                },
                {
                    "object": "database",
                    "id": "d1",
                    "url": "https://notion.so/d1",
                    "title": [{"plain_text": "Tarefas"}],
                },
            ],
            "has_more": False,
        },
        status=200,
    )
    itens = svc.buscar("x", cliente=_cliente())
    assert itens[0] == {
        "id": "p1",
        "tipo": "page",
        "titulo": "Nota",
        "url": "https://notion.so/p1",
    }
    assert itens[1]["titulo"] == "Tarefas"


@responses.activate
def test_listar_linhas_resolve_data_sources():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/databases/db1",
        json={"data_sources": [{"id": "ds1", "name": "Principal"}]},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/data_sources/ds1/query",
        json={
            "results": [
                {
                    "id": "r1",
                    "url": "https://notion.so/r1",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Linha 1"}]}
                    },
                }
            ],
            "has_more": False,
        },
        status=200,
    )
    linhas = svc.listar_linhas("db1", cliente=_cliente())
    assert linhas == [{"id": "r1", "titulo": "Linha 1", "url": "https://notion.so/r1"}]


@responses.activate
def test_listar_linhas_sem_data_source_acessivel_retorna_vazio():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/databases/db1",
        json={"data_sources": []},
        status=200,
    )
    assert svc.listar_linhas("db1", cliente=_cliente()) == []


@responses.activate
def test_ler_pagina_ou_database_pagina_com_corpo():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/blocks/page1/children",
        json={
            "results": [
                {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "oi"}]}}
            ],
            "has_more": False,
        },
        status=200,
    )
    resultado = svc.ler_pagina_ou_database("page1", cliente=_cliente())
    assert resultado == {
        "id": "page1",
        "tipo": "pagina",
        "propriedades": {},
        "markdown": "oi",
    }


@responses.activate
def test_ler_pagina_ou_database_detecta_database():
    # corpo vazio -> tenta linhas
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/blocks/db1/children",
        json={"results": [], "has_more": False},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/databases/db1",
        json={"data_sources": [{"id": "ds1", "name": "Principal"}]},
        status=200,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/data_sources/ds1/query",
        json={
            "results": [
                {
                    "id": "r1",
                    "url": "https://notion.so/r1",
                    "properties": {
                        "Name": {"type": "title", "title": [{"plain_text": "Linha 1"}]}
                    },
                }
            ],
            "has_more": False,
        },
        status=200,
    )
    resultado = svc.ler_pagina_ou_database("db1", cliente=_cliente())
    assert resultado["tipo"] == "database"
    assert resultado["linhas"][0]["titulo"] == "Linha 1"


@responses.activate
def test_ler_pagina_ou_database_pagina_sem_corpo():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/blocks/page1/children",
        json={"results": [], "has_more": False},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/databases/page1",
        json={"data_sources": []},
        status=200,
    )
    resultado = svc.ler_pagina_ou_database("page1", cliente=_cliente())
    assert resultado == {
        "id": "page1",
        "tipo": "pagina",
        "propriedades": {},
        "markdown": "",
    }


@responses.activate
def test_ler_pagina_ou_database_traz_propriedades_preenchidas_primeiro():
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/pages/page1",
        json={
            "id": "page1",
            "properties": {
                "Nome": {"type": "title", "title": [{"plain_text": "Linha"}]},
                "Status": {"type": "status", "status": {"name": "Feito"}},
                "Prazo": {"type": "date", "date": None},
            },
        },
        status=200,
    )
    responses.add(
        responses.GET,
        f"{NOTION_BASE_URL}/blocks/page1/children",
        json={"results": [], "has_more": False},
        status=200,
    )
    resultado = svc.ler_pagina_ou_database("page1", cliente=_cliente())
    # Propriedades preenchidas entram (vazias ficam de fora), mesmo sem corpo.
    assert resultado["tipo"] == "pagina"
    assert resultado["propriedades"] == {"Nome": "Linha", "Status": "Feito"}
    assert resultado["markdown"] == ""
