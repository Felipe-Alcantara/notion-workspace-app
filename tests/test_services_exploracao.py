"""Testes da exploração genérica de databases (``services.exploracao``).

O coração desta camada é converter QUALQUER tipo de coluna do Notion em texto
sem quebrar. Os testes cobrem os tipos comuns, a unificação de colunas (título
primeiro) e o caso de database sem data source acessível.
"""

from __future__ import annotations

from services import exploracao as svc

DB_ID = "db1"
FONTE_ID = "ds1"

SCHEMA = {
    "Nome": {"type": "title", "title": {}},
    "Etapa": {"type": "status", "status": {}},
    "Tags": {"type": "multi_select", "multi_select": {}},
    "Prazo": {"type": "date", "date": {}},
    "Feito": {"type": "checkbox", "checkbox": {}},
    "Valor": {"type": "number", "number": {}},
    "Relacionado": {"type": "relation", "relation": {}},
    "Botao": {"type": "button", "button": {}},
}


class FakeClient:
    def __init__(self, fontes=None, linhas=None):
        self._fontes = fontes if fontes is not None else [{"id": FONTE_ID, "name": "Fonte"}]
        self._linhas = linhas or []

    def buscar(self, query=None, buscar_todos=False, filtro=None):
        return [
            {"id": "dbA", "object": "database", "title": [{"plain_text": "Zebra"}], "url": "u1"},
            {"id": "dbB", "object": "database", "title": [{"plain_text": "Alfa"}], "url": "u2"},
        ]

    def listar_data_sources(self, database_id):
        return self._fontes

    def get_data_source(self, data_source_id):
        return {"properties": SCHEMA}

    def consultar_data_source(self, data_source_id, buscar_todos=False, **kwargs):
        return self._linhas


def test_listar_databases_ordena_por_titulo():
    itens = svc.listar_databases(cliente=FakeClient())
    assert [d["titulo"] for d in itens] == ["Alfa", "Zebra"]


def test_descrever_database_sem_fonte_volta_vazio():
    resultado = svc.descrever_database(DB_ID, cliente=FakeClient(fontes=[]))
    assert resultado == {"id": DB_ID, "colunas": [], "linhas": []}


def test_colunas_titulo_primeiro_e_button_oculto():
    resultado = svc.descrever_database(DB_ID, cliente=FakeClient())
    nomes = [c["nome"] for c in resultado["colunas"]]
    assert nomes[0] == "Nome"  # title sempre primeiro
    assert "Botao" not in nomes  # button é oculto


def test_linha_converte_todos_os_tipos_em_texto():
    linha = {
        "id": "r1",
        "url": "https://notion.so/r1",
        "properties": {
            "Nome": {"type": "title", "title": [{"plain_text": "Tarefa X"}]},
            "Etapa": {"type": "status", "status": {"name": "Entrada"}},
            "Tags": {"type": "multi_select", "multi_select": [{"name": "a"}, {"name": "b"}]},
            "Prazo": {"type": "date", "date": {"start": "2026-07-01"}},
            "Feito": {"type": "checkbox", "checkbox": True},
            "Valor": {"type": "number", "number": 42},
            "Relacionado": {"type": "relation", "relation": [{"id": "x"}, {"id": "y"}]},
        },
    }
    resultado = svc.descrever_database(DB_ID, cliente=FakeClient(linhas=[linha]))
    valores = resultado["linhas"][0]["valores"]
    assert valores["Nome"] == "Tarefa X"
    assert valores["Etapa"] == "Entrada"
    assert valores["Tags"] == "a, b"
    assert valores["Prazo"] == "2026-07-01"
    assert valores["Feito"] == "✓"
    assert valores["Valor"] == "42"
    assert valores["Relacionado"] == "2 vínculo(s)"


def test_data_com_intervalo():
    linha = {
        "id": "r1",
        "properties": {
            "Nome": {"type": "title", "title": []},
            "Prazo": {"type": "date", "date": {"start": "2026-07-01", "end": "2026-07-05"}},
        },
    }
    resultado = svc.descrever_database(DB_ID, cliente=FakeClient(linhas=[linha]))
    assert resultado["linhas"][0]["valores"]["Prazo"] == "2026-07-01 → 2026-07-05"


def test_propriedade_ausente_ou_desconhecida_vira_vazio():
    linha = {
        "id": "r1",
        "properties": {
            "Nome": {"type": "title", "title": [{"plain_text": "Y"}]},
            # Etapa/Tags/etc. ausentes -> texto vazio, sem quebrar
        },
    }
    resultado = svc.descrever_database(DB_ID, cliente=FakeClient(linhas=[linha]))
    valores = resultado["linhas"][0]["valores"]
    assert valores["Etapa"] == ""
    assert valores["Tags"] == ""
    assert valores["Nome"] == "Y"
