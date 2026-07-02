"""Testes do caso de uso de normalização de nomes (``services.normalizacao``).

A lógica de migração vivia na borda (CLI) e foi movida para o serviço. Estes
testes a exercitam diretamente com um cliente falso, afirmando o contrato do
dry-run (não escreve) e da aplicação (renomeia propriedades, traduz opções e
migra valores de linha).
"""

from __future__ import annotations

from services import normalizacao as svc

DATABASE_ID = "db_tarefas"
AREAS_DB_ID = "db_areas"


class FakeClient:
    """Cliente falso que grava escritas e devolve um schema de template."""

    def __init__(self) -> None:
        self.escritas: list[tuple[str, tuple]] = []

    def get_database(self, database_id):
        if database_id == DATABASE_ID:
            return {
                "title": [{"plain_text": "Tarefas"}],
                "properties": {
                    "Status": {
                        "type": "status",
                        "status": {
                            "options": [
                                {"id": "o1", "name": "00. Inbox", "color": "blue"},
                                {"id": "o2", "name": "06. Feito", "color": "green"},
                            ],
                            "groups": [{"name": "To-do", "option_ids": ["o1"]}],
                        },
                    },
                    "Áreas-da-Vida": {
                        "type": "relation",
                        "relation": {"database_id": AREAS_DB_ID},
                    },
                },
            }
        if database_id == AREAS_DB_ID:
            return {
                "title": [{"plain_text": "Areas"}],
                "properties": {"Name": {"type": "title"}},
            }
        return {"title": [], "properties": {}}

    def consultar_database(self, database_id, buscar_todos=False, **kwargs):
        if database_id == DATABASE_ID:
            return [
                {
                    "id": "linha1",
                    "properties": {
                        "Status": {"type": "status", "status": {"name": "00. Inbox"}}
                    },
                }
            ]
        if database_id == AREAS_DB_ID:
            return [
                {
                    "id": "area1",
                    "properties": {"Name": {"title": [{"plain_text": "Money"}]}},
                }
            ]
        return []

    def atualizar_database(self, database_id, *, titulo=None, propriedades=None):
        self.escritas.append(("db", (database_id, titulo, propriedades)))
        return {"id": database_id}

    def atualizar_pagina(self, page_id, propriedades):
        self.escritas.append(("pagina", (page_id, propriedades)))
        return {"id": page_id}


def test_dry_run_nao_escreve_mas_relata():
    cli = FakeClient()
    relatorio = svc.normalizar_nomes(DATABASE_ID, aplicar=False, cliente=cli)

    assert cli.escritas == []  # dry-run não toca o Notion
    assert relatorio["aplicado"] is False
    # ainda assim calcula o que mudaria.
    assert {"de": "00. Inbox", "para": "Entrada"} in relatorio["opcoes_adicionadas"]["status"]
    assert relatorio["paginas_alteradas"] == 1
    propriedades = {p["de"]: p["para"] for p in relatorio["propriedades_renomeadas"]}
    assert propriedades["Status"] == "Etapa"
    assert propriedades["Áreas-da-Vida"] == "Áreas da vida"


def test_aplicar_escreve_no_notion():
    cli = FakeClient()
    relatorio = svc.normalizar_nomes(DATABASE_ID, aplicar=True, cliente=cli)

    assert relatorio["aplicado"] is True
    assert cli.escritas  # houve escrita
    # migrou a linha de status.
    paginas = [e for e in cli.escritas if e[0] == "pagina"]
    assert any(pid == "linha1" for _, (pid, _) in paginas)


def test_normaliza_areas_relacionadas():
    cli = FakeClient()
    relatorio = svc.normalizar_nomes(DATABASE_ID, aplicar=False, cliente=cli)
    areas = relatorio["areas"]
    assert areas["database_id"] == AREAS_DB_ID
    assert {"de": "Money", "para": "Finanças"} in areas["paginas_renomeadas"]


def test_propriedade_resolvida_em_qualquer_estado():
    # Quando a propriedade já está no nome novo, não há o que renomear.
    class JaNormalizado(FakeClient):
        def get_database(self, database_id):
            if database_id == DATABASE_ID:
                return {
                    "title": [{"plain_text": "Tarefas"}],
                    "properties": {"Etapa": {"type": "status", "status": {"options": []}}},
                }
            return {"title": [], "properties": {}}

        def consultar_database(self, database_id, buscar_todos=False, **kwargs):
            return []

    relatorio = svc.normalizar_nomes(DATABASE_ID, aplicar=False, cliente=JaNormalizado())
    assert relatorio["propriedades_renomeadas"] == []
    assert relatorio["paginas_alteradas"] == 0
