"""Testes dos casos de uso de páginas de projeto."""

from __future__ import annotations

from integrations.github import RepoInfo
from services.projetos import ProjetoAtualizado, atualizar_pagina_projeto
from services.sincronizar_github import CamposProjeto


class _NotionFixo:
    def __init__(self) -> None:
        self.atualizacoes: list[tuple[str, dict]] = []

    def atualizar_pagina(self, page_id: str, propriedades: dict) -> dict:
        self.atualizacoes.append((page_id, propriedades))
        return {"id": page_id, "url": f"https://notion.so/{page_id}"}


def _repo() -> RepoInfo:
    return RepoInfo(
        nome="projeto",
        nome_completo="felipe/projeto",
        descricao="Estado atual do projeto",
        url_html="https://github.com/felipe/projeto",
        linguagem="Python",
        topicos=["notion", "mcp"],
        estrelas=3,
        forks=1,
    )


def test_atualizar_pagina_projeto_delega_ao_notion():
    notion = _NotionFixo()
    resultado = atualizar_pagina_projeto(
        "pagina-1",
        _repo(),
        notion_client=notion,
    )
    assert resultado == ProjetoAtualizado(
        id="pagina-1",
        url="https://notion.so/pagina-1",
    )
    page_id, propriedades = notion.atualizacoes[0]
    assert page_id == "pagina-1"
    assert propriedades["Nome"]["title"][0]["text"]["content"] == "felipe/projeto"
    assert propriedades["Descrição"]["rich_text"][0]["text"]["content"] == (
        "Estado atual do projeto"
    )


def test_atualizar_pagina_projeto_aceita_campos_customizados():
    notion = _NotionFixo()
    atualizar_pagina_projeto(
        "pagina-2",
        _repo(),
        notion_client=notion,
        campos=CamposProjeto(nome="Projeto", descricao="Resumo"),
    )
    propriedades = notion.atualizacoes[0][1]
    assert "Projeto" in propriedades
    assert "Resumo" in propriedades
    assert "Nome" not in propriedades
