"""Testes do caso de uso GitHub → Notion."""

from __future__ import annotations

import pytest
from integrations.github import RepoInfo
from services.sincronizar_github import (
    CamposProjeto,
    ResumoSync,
    _propriedades_pagina,
    _propriedades_tarefa,
    sincronizar,
)

from notion_starter import Tarefa

DB_PROJ = "db_projetos"


def _repo(nome: str = "r1", **extras) -> RepoInfo:
    dados = {
        "nome": nome,
        "nome_completo": f"felipe/{nome}",
        "descricao": "Descrição do repo",
        "url_html": f"https://github.com/felipe/{nome}",
        "homepage": "https://example.com",
        "linguagem": "Python",
        "topicos": ["notion"],
        "estrelas": 10,
        "forks": 2,
        "privado": False,
        "atualizado_em": "2026-06-25T00:00:00Z",
    }
    dados.update(extras)
    return RepoInfo(**dados)


class _GitHubFixo:
    def __init__(self, repos: list[RepoInfo]) -> None:
        self.repos = repos

    def listar_repos(self, usuario: str) -> list[RepoInfo]:
        assert usuario == "felipe"
        return self.repos


class _NotionFixo:
    def __init__(
        self,
        *,
        existentes: dict[str, str] | None = None,
        falhar_criacao: bool = False,
    ) -> None:
        self.existentes = existentes or {}
        self.falhar_criacao = falhar_criacao
        self.criados: list[tuple[str, dict]] = []
        self.atualizados: list[tuple[str, dict]] = []

    def consultar_database(self, database_id, page_size=100, filtro=None):
        assert database_id == DB_PROJ
        assert page_size == 1
        url = filtro.get("url", {}).get("equals")
        page_id = self.existentes.get(url)
        return [{"id": page_id}] if page_id else []

    def criar_pagina(self, database_id, propriedades):
        if self.falhar_criacao:
            raise RuntimeError("falha no Notion")
        self.criados.append((database_id, propriedades))
        return {"id": "nova"}

    def atualizar_pagina(self, page_id, propriedades):
        self.atualizados.append((page_id, propriedades))
        return {"id": page_id}


class _TaskListFixa:
    def __init__(
        self,
        *,
        nomes_existentes: list[str] | None = None,
        falhar_criacao: bool = False,
    ) -> None:
        self.nomes_existentes = nomes_existentes or []
        self.falhar_criacao = falhar_criacao
        self.criadas: list[tuple[str, str | None]] = []

    def listar(self):
        return [
            Tarefa(id=f"t-{indice}", nome=nome) for indice, nome in enumerate(self.nomes_existentes)
        ]

    def criar(self, nome, status=None, prazo=None):
        if self.falhar_criacao:
            raise RuntimeError("falha na tarefa")
        self.criadas.append((nome, status))
        return Tarefa(id="nova", nome=nome, status=status)


def test_propriedades_pagina_monta_campos_completos():
    props = _propriedades_pagina(_repo())
    assert props["Nome"]["title"][0]["text"]["content"] == "felipe/r1"
    assert props["Descrição"]["rich_text"][0]["text"]["content"] == "Descrição do repo"
    assert props["URL"]["url"] == "https://github.com/felipe/r1"
    assert props["Homepage"]["url"] == "https://example.com"
    assert props["Linguagem"]["select"]["name"] == "Python"
    assert props["Privado"]["checkbox"] is False
    assert props["Atualizado em"]["date"]["start"] == "2026-06-25T00:00:00Z"


def test_propriedades_pagina_aceita_nomes_de_coluna_customizados():
    campos = CamposProjeto(nome="Projeto", url="Repositório")
    props = _propriedades_pagina(_repo(), campos)
    assert "Projeto" in props
    assert "Repositório" in props
    assert "Nome" not in props


def test_propriedades_tarefa_formato():
    props = _propriedades_tarefa(_repo("meu-repo"))
    conteudo = props["Nome"]["title"][0]["text"]["content"]
    assert conteudo == "Revisar repo: meu-repo"


def test_sincronizar_cria_pagina_e_tarefa_por_repo():
    notion = _NotionFixo()
    tasklist = _TaskListFixa()
    resumo = sincronizar(
        "felipe",
        github_client=_GitHubFixo([_repo("r1"), _repo("r2")]),
        notion_client=notion,
        tasklist=tasklist,
        database_projetos_id=DB_PROJ,
        status_tarefa="Backlog",
    )
    assert resumo.repos_encontrados == 2
    assert resumo.paginas_criadas == 2
    assert resumo.tarefas_criadas == 2
    assert resumo.erros == 0
    assert tasklist.criadas == [
        ("Revisar repo: r1", "Backlog"),
        ("Revisar repo: r2", "Backlog"),
    ]


def test_sincronizar_atualiza_pagina_e_nao_duplica_tarefa():
    repo = _repo()
    notion = _NotionFixo(existentes={repo.url_html: "pagina-1"})
    tasklist = _TaskListFixa(nomes_existentes=["Revisar repo: r1"])
    resumo = sincronizar(
        "felipe",
        github_client=_GitHubFixo([repo]),
        notion_client=notion,
        tasklist=tasklist,
        database_projetos_id=DB_PROJ,
    )
    assert resumo.paginas_atualizadas == 1
    assert resumo.paginas_criadas == 0
    assert resumo.tarefas_existentes == 1
    assert resumo.tarefas_criadas == 0
    assert notion.atualizados[0][0] == "pagina-1"


def test_sincronizar_contabiliza_falhas_independentes():
    resumo = sincronizar(
        "felipe",
        github_client=_GitHubFixo([_repo()]),
        notion_client=_NotionFixo(falhar_criacao=True),
        tasklist=_TaskListFixa(falhar_criacao=True),
        database_projetos_id=DB_PROJ,
    )
    assert resumo.paginas_criadas == 0
    assert resumo.tarefas_criadas == 0
    assert resumo.erros == 2


def test_sincronizar_sem_repos():
    resumo = sincronizar(
        "felipe",
        github_client=_GitHubFixo([]),
        notion_client=_NotionFixo(),
        tasklist=_TaskListFixa(),
        database_projetos_id=DB_PROJ,
    )
    assert resumo == ResumoSync()


def test_sincronizar_exige_database_de_projetos(monkeypatch):
    monkeypatch.delenv("NOTION_PROJECTS_DATABASE_ID", raising=False)
    with pytest.raises(ValueError, match="database_projetos_id"):
        sincronizar(
            "felipe",
            github_client=_GitHubFixo([]),
            notion_client=_NotionFixo(),
            tasklist=_TaskListFixa(),
        )


def test_sincronizar_exige_database_de_tarefas_sem_tasklist(monkeypatch):
    monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
    with pytest.raises(ValueError, match="database_tarefas_id"):
        sincronizar(
            "felipe",
            github_client=_GitHubFixo([]),
            notion_client=_NotionFixo(),
            database_projetos_id=DB_PROJ,
        )


def test_resumo_sync_defaults():
    assert ResumoSync() == ResumoSync(
        repos_encontrados=0,
        paginas_criadas=0,
        paginas_atualizadas=0,
        tarefas_criadas=0,
        tarefas_existentes=0,
        erros=0,
    )
