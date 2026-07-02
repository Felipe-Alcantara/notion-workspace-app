"""Testes do caso de uso de inventário GitHub → database do Notion."""

from __future__ import annotations

import pytest
from integrations.github import RepoInfo
from services.inventario_github import (
    CamposGitHub,
    ResumoInventario,
    _hash_readme,
    _propriedades_pagina,
    atualizar_repos,
    construir_schema,
    exportar_repos,
    garantir_coluna_hash,
    garantir_database,
)

DB = "db_github"
PAGINA_HOME = "pagina-home"


def _repo(nome: str = "r1", *, dono: str = "felipe", **extras) -> RepoInfo:
    dados = {
        "nome": nome,
        "nome_completo": f"{dono}/{nome}",
        "descricao": "Descrição do repo",
        "url_html": f"https://github.com/{dono}/{nome}",
        "homepage": "https://example.com",
        "linguagem": "Python",
        "topicos": ["notion"],
        "estrelas": 10,
        "forks": 2,
        "issues_abertas": 3,
        "tamanho_kb": 42,
        "privado": False,
        "fork": False,
        "arquivado": False,
        "licenca": "MIT",
        "dono": dono,
        "criado_em": "2026-01-01T00:00:00Z",
        "atualizado_em": "2026-06-25T00:00:00Z",
        "enviado_em": "2026-06-26T00:00:00Z",
    }
    dados.update(extras)
    return RepoInfo(**dados)


class _GitHubFixo:
    def __init__(
        self,
        repos_por_conta: dict[str, list[RepoInfo]],
        *,
        readmes: dict[str, str] | None = None,
        falhar_listar: set[str] | None = None,
    ) -> None:
        self.repos_por_conta = repos_por_conta
        self.readmes = readmes or {}
        self.falhar_listar = falhar_listar or set()
        self.detalhados: list[str] = []

    def listar_repos(self, usuario: str) -> list[RepoInfo]:
        if usuario in self.falhar_listar:
            raise RuntimeError("falha ao listar")
        return self.repos_por_conta.get(usuario, [])

    def detalhar_repo(self, repo_completo: str) -> RepoInfo:
        self.detalhados.append(repo_completo)
        base = _repo(repo_completo.split("/")[-1])
        base.readme = self.readmes.get(repo_completo)
        return base


def _rt(texto: str) -> dict:
    """Propriedade rich_text como a API do Notion devolve (com plain_text)."""
    if not texto:
        return {"rich_text": []}
    return {"rich_text": [{"plain_text": texto, "text": {"content": texto}}]}


class _NotionFixo:
    def __init__(
        self,
        *,
        existentes: dict[str, str] | None = None,
        falhar_criacao: bool = False,
        hashes: dict[str, str] | None = None,
        blocos: dict[str, list] | None = None,
        tem_coluna_hash: bool = True,
        sem_data_source: bool = False,
    ) -> None:
        # existentes: {url -> page_id}. hashes/blocos: por page_id.
        self.existentes = existentes or {}
        self.falhar_criacao = falhar_criacao
        self.hashes = hashes or {}
        self.blocos = blocos or {}
        self.tem_coluna_hash = tem_coluna_hash
        self.sem_data_source = sem_data_source
        self.colunas_criadas: list[dict] = []
        self.criados: list[tuple[str, dict]] = []
        self.atualizados: list[tuple[str, dict]] = []
        self.subpaginas: list[tuple[str, str, list]] = []
        self.databases_criados: list[tuple[str, str]] = []
        self.blocos_excluidos: list[str] = []

    def criar_database(self, pagina_id, titulo, propriedades):
        self.databases_criados.append((pagina_id, titulo))
        return {"id": DB}

    def consultar_database(self, database_id, page_size=100, filtro=None):
        assert database_id == DB
        url = filtro.get("url", {}).get("equals")
        page_id = self.existentes.get(url)
        if not page_id:
            return []
        props = {"README hash": _rt(self.hashes.get(page_id, ""))}
        return [{"id": page_id, "properties": props}]

    def criar_pagina(self, database_id, propriedades):
        if self.falhar_criacao:
            raise RuntimeError("falha no Notion")
        page_id = f"pagina-{len(self.criados)}"
        self.criados.append((database_id, propriedades))
        return {"id": page_id}

    def atualizar_pagina(self, page_id, propriedades):
        self.atualizados.append((page_id, propriedades))
        return {"id": page_id}

    def criar_subpagina(self, pagina_pai_id, titulo, *, blocos=None):
        self.subpaginas.append((pagina_pai_id, titulo, blocos or []))
        return {"id": f"sub-{len(self.subpaginas)}"}

    def ler_blocos(self, block_id, *a, **k):
        return self.blocos.get(block_id, [])

    def excluir_bloco(self, block_id):
        self.blocos_excluidos.append(block_id)
        return {"id": block_id}

    # -- Schema (para garantir_coluna_hash) --------------------------------

    def _props_schema(self):
        return {"README hash": {"rich_text": {}}} if self.tem_coluna_hash else {}

    def listar_data_sources(self, database_id):
        return [] if self.sem_data_source else [{"id": "ds-1", "name": "GITHUB"}]

    def get_data_source(self, data_source_id):
        return {"id": data_source_id, "properties": self._props_schema()}

    def atualizar_data_source(self, data_source_id, *, propriedades):
        self.colunas_criadas.append(propriedades)
        self.tem_coluna_hash = True
        return {"id": data_source_id, "properties": self._props_schema()}

    def get_database(self, database_id):
        return {"id": database_id, "properties": self._props_schema()}

    def atualizar_database(self, database_id, *, titulo=None, propriedades=None):
        self.colunas_criadas.append(propriedades)
        self.tem_coluna_hash = True
        return {"id": database_id, "properties": self._props_schema()}


# --------------------------------------------------------------------------- #
# Schema e mapeamento
# --------------------------------------------------------------------------- #


def test_schema_tem_title_e_colunas_uteis():
    schema = construir_schema()
    assert schema["Nome"] == {"title": {}}
    for coluna in ("Estrelas", "Licença", "Privado", "Último push", "Conta"):
        assert coluna in schema


def test_schema_respeita_nomes_customizados():
    schema = construir_schema(CamposGitHub(nome="Projeto", estrelas="Stars"))
    assert "Projeto" in schema and schema["Projeto"] == {"title": {}}
    assert "Stars" in schema
    assert "Nome" not in schema


def test_propriedades_pagina_monta_campos_completos():
    props = _propriedades_pagina(_repo(), CamposGitHub())
    assert props["Nome"]["title"][0]["text"]["content"] == "felipe/r1"
    assert props["Conta"]["select"]["name"] == "felipe"
    assert props["Linguagem"]["select"]["name"] == "Python"
    assert props["Licença"]["select"]["name"] == "MIT"
    assert props["Issues abertas"]["number"] == 3
    assert props["Fork"]["checkbox"] is False
    assert props["Último push"]["date"]["start"] == "2026-06-26T00:00:00Z"


def test_propriedades_pagina_omite_opcionais_ausentes():
    repo = _repo(linguagem=None, licenca=None, homepage=None, topicos=[])
    props = _propriedades_pagina(repo, CamposGitHub())
    assert "Linguagem" not in props
    assert "Licença" not in props
    assert "Homepage" not in props
    assert "Tópicos" not in props


# --------------------------------------------------------------------------- #
# garantir_database
# --------------------------------------------------------------------------- #


def test_garantir_database_cria_sob_a_pagina():
    notion = _NotionFixo()
    db_id = garantir_database(PAGINA_HOME, cliente=notion, titulo="GITHUB")
    assert db_id == DB
    assert notion.databases_criados == [(PAGINA_HOME, "GITHUB")]


# --------------------------------------------------------------------------- #
# exportar_repos
# --------------------------------------------------------------------------- #


def test_exportar_cria_pagina_e_subpagina_readme():
    notion = _NotionFixo()
    github = _GitHubFixo(
        {"felipe": [_repo("r1")]},
        readmes={"felipe/r1": "# Olá\n\nConteúdo do README."},
    )
    resumo = exportar_repos(
        ["felipe"], DB, github_client=github, notion_client=notion
    )
    assert resumo.repos_encontrados == 1
    assert resumo.paginas_criadas == 1
    assert resumo.readmes_escritos == 1
    assert resumo.total_erros == 0
    assert github.detalhados == ["felipe/r1"]
    # README vai para uma subpágina filha chamada "README", não para o corpo.
    assert len(notion.subpaginas) == 1
    pai, titulo, blocos = notion.subpaginas[0]
    assert pai == "pagina-0"
    assert titulo == "README"
    assert blocos


def test_exportar_atualiza_existente_e_nao_escreve_readme():
    repo = _repo("r1")
    notion = _NotionFixo(existentes={repo.url_html: "pagina-existente"})
    github = _GitHubFixo({"felipe": [repo]}, readmes={"felipe/r1": "# README"})
    resumo = exportar_repos(
        ["felipe"], DB, github_client=github, notion_client=notion
    )
    assert resumo.paginas_atualizadas == 1
    assert resumo.paginas_criadas == 0
    assert resumo.readmes_escritos == 0
    assert notion.atualizados[0][0] == "pagina-existente"
    assert notion.subpaginas == []  # não recria README em página existente


def test_exportar_deduplica_repos_entre_contas():
    repo = _repo("compartilhado")
    notion = _NotionFixo()
    github = _GitHubFixo({"conta-a": [repo], "conta-b": [repo]})
    resumo = exportar_repos(
        ["conta-a", "conta-b"],
        DB,
        github_client=github,
        notion_client=notion,
        incluir_readme=False,
    )
    assert resumo.repos_encontrados == 1
    assert resumo.paginas_criadas == 1


def test_exportar_sem_readme_nao_detalha():
    notion = _NotionFixo()
    github = _GitHubFixo({"felipe": [_repo("r1")]})
    resumo = exportar_repos(
        ["felipe"],
        DB,
        github_client=github,
        notion_client=notion,
        incluir_readme=False,
    )
    assert resumo.paginas_criadas == 1
    assert github.detalhados == []
    assert notion.subpaginas == []


def test_exportar_registra_falha_de_listar_e_segue():
    notion = _NotionFixo()
    github = _GitHubFixo({"boa": [_repo("r1")]}, falhar_listar={"ruim"})
    resumo = exportar_repos(
        ["ruim", "boa"],
        DB,
        github_client=github,
        notion_client=notion,
        incluir_readme=False,
    )
    assert resumo.paginas_criadas == 1
    assert resumo.total_erros == 1
    assert "listar ruim" in resumo.erros[0]


def test_exportar_falha_de_criacao_nao_interrompe():
    notion = _NotionFixo(falhar_criacao=True)
    github = _GitHubFixo({"felipe": [_repo("r1"), _repo("r2")]})
    resumo = exportar_repos(
        ["felipe"],
        DB,
        github_client=github,
        notion_client=notion,
        incluir_readme=False,
    )
    assert resumo.paginas_criadas == 0
    assert resumo.total_erros == 2


def test_exportar_exige_contas():
    with pytest.raises(ValueError, match="conta"):
        exportar_repos([], DB, github_client=_GitHubFixo({}), notion_client=_NotionFixo())


def test_exportar_exige_database():
    with pytest.raises(ValueError, match="database_id"):
        exportar_repos(
            ["felipe"], "", github_client=_GitHubFixo({}), notion_client=_NotionFixo()
        )


def test_resumo_inventario_defaults():
    r = ResumoInventario()
    assert r.repos_encontrados == 0
    assert r.readmes_atualizados == 0
    assert r.total_erros == 0


# --------------------------------------------------------------------------- #
# atualizar_repos
# --------------------------------------------------------------------------- #


def _readme_child(block_id="blk-readme"):
    return {"id": block_id, "type": "child_page", "child_page": {"title": "README"}}


def test_schema_inclui_readme_hash():
    assert "README hash" in construir_schema()


def test_atualizar_cria_repo_novo_com_readme_e_hash():
    notion = _NotionFixo()
    github = _GitHubFixo({"felipe": [_repo("novo")]}, readmes={"felipe/novo": "# Oi"})
    resumo = atualizar_repos(["felipe"], DB, github_client=github, notion_client=notion)
    assert resumo.paginas_criadas == 1
    assert resumo.readmes_escritos == 1
    assert notion.subpaginas  # README criado
    # Hash gravado na página recém-criada (via atualizar_pagina após criar).
    assert any("README hash" in props for _, props in notion.atualizados)


def test_atualizar_existente_readme_inalterado_nao_recria():
    repo = _repo("r1")
    readme = "# Mesmo conteúdo"
    h = _hash_readme(readme)
    notion = _NotionFixo(
        existentes={repo.url_html: "pagina-1"},
        hashes={"pagina-1": h},
        blocos={"pagina-1": [_readme_child()]},
    )
    github = _GitHubFixo({"felipe": [repo]}, readmes={"felipe/r1": readme})
    resumo = atualizar_repos(["felipe"], DB, github_client=github, notion_client=notion)
    assert resumo.paginas_atualizadas == 1
    assert resumo.readmes_atualizados == 0
    assert notion.blocos_excluidos == []  # não apagou a subpágina
    assert notion.subpaginas == []  # não recriou


def test_atualizar_existente_readme_mudou_substitui_subpagina():
    repo = _repo("r1")
    notion = _NotionFixo(
        existentes={repo.url_html: "pagina-1"},
        hashes={"pagina-1": "hashantigo000000"},
        blocos={"pagina-1": [_readme_child("blk-velho")]},
    )
    github = _GitHubFixo({"felipe": [repo]}, readmes={"felipe/r1": "# Conteúdo NOVO"})
    resumo = atualizar_repos(["felipe"], DB, github_client=github, notion_client=notion)
    assert resumo.paginas_atualizadas == 1
    assert resumo.readmes_atualizados == 1
    assert notion.blocos_excluidos == ["blk-velho"]  # apagou a antiga
    assert notion.subpaginas  # recriou


def test_atualizar_remove_readmes_duplicados_antes_de_recriar():
    # Execuções anteriores podem ter deixado 2 subpáginas README; todas saem.
    repo = _repo("r1")
    notion = _NotionFixo(
        existentes={repo.url_html: "pagina-1"},
        hashes={"pagina-1": "hashantigo000000"},
        blocos={"pagina-1": [_readme_child("blk-a"), _readme_child("blk-b")]},
    )
    github = _GitHubFixo({"felipe": [repo]}, readmes={"felipe/r1": "# NOVO"})
    resumo = atualizar_repos(["felipe"], DB, github_client=github, notion_client=notion)
    assert resumo.readmes_atualizados == 1
    assert notion.blocos_excluidos == ["blk-a", "blk-b"]  # apagou as duas
    assert len(notion.subpaginas) == 1  # recriou só uma


def test_atualizar_sem_readme_so_propriedades():
    repo = _repo("r1")
    notion = _NotionFixo(existentes={repo.url_html: "pagina-1"})
    github = _GitHubFixo({"felipe": [repo]}, readmes={"felipe/r1": "# X"})
    resumo = atualizar_repos(
        ["felipe"], DB, github_client=github, notion_client=notion, sincronizar_readme=False
    )
    assert resumo.paginas_atualizadas == 1
    assert resumo.readmes_atualizados == 0
    assert github.detalhados == []  # não foi buscar o README
    assert notion.blocos_excluidos == []


def test_atualizar_exige_contas_e_database():
    with pytest.raises(ValueError, match="conta"):
        atualizar_repos([], DB, github_client=_GitHubFixo({}), notion_client=_NotionFixo())
    with pytest.raises(ValueError, match="database_id"):
        atualizar_repos(
            ["felipe"], "", github_client=_GitHubFixo({}), notion_client=_NotionFixo()
        )


# --------------------------------------------------------------------------- #
# garantir_coluna_hash
# --------------------------------------------------------------------------- #


def test_garantir_coluna_hash_cria_quando_falta_no_data_source():
    notion = _NotionFixo(tem_coluna_hash=False)
    criou = garantir_coluna_hash(DB, cliente=notion)
    assert criou is True
    assert notion.colunas_criadas == [{"README hash": {"rich_text": {}}}]


def test_garantir_coluna_hash_idempotente_quando_ja_existe():
    notion = _NotionFixo(tem_coluna_hash=True)
    criou = garantir_coluna_hash(DB, cliente=notion)
    assert criou is False
    assert notion.colunas_criadas == []


def test_garantir_coluna_hash_usa_database_quando_nao_ha_data_source():
    notion = _NotionFixo(tem_coluna_hash=False, sem_data_source=True)
    criou = garantir_coluna_hash(DB, cliente=notion)
    assert criou is True
    assert notion.colunas_criadas == [{"README hash": {"rich_text": {}}}]


def test_atualizar_garante_coluna_hash_antes_de_gravar():
    notion = _NotionFixo(tem_coluna_hash=False)
    github = _GitHubFixo({"felipe": [_repo("r1")]}, readmes={"felipe/r1": "# X"})
    atualizar_repos(["felipe"], DB, github_client=github, notion_client=notion)
    # A coluna foi criada uma vez, antes de processar os repos.
    assert notion.colunas_criadas == [{"README hash": {"rich_text": {}}}]


def test_atualizar_sem_readme_nao_mexe_no_schema():
    notion = _NotionFixo(tem_coluna_hash=False)
    github = _GitHubFixo({"felipe": [_repo("r1")]})
    atualizar_repos(
        ["felipe"], DB, github_client=github, notion_client=notion, sincronizar_readme=False
    )
    assert notion.colunas_criadas == []
