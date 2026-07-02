"""Testes da ingestão de fontes, sem rede real."""

from __future__ import annotations

from pathlib import Path

import pytest
import responses
from integrations.github import RepoInfo
from services.ingestao import (
    Fonte,
    FonteArquivos,
    FonteGitHub,
    ItemColetado,
    _propriedades_de_item,
    ingerir,
)

from notion_starter import NotionClient
from notion_starter.constants import NOTION_BASE_URL

TOKEN = "ntn_test_token"
DB = "db_ingestao"


def _pagina_resposta(id_: str, nome: str = "item") -> dict:
    return {
        "id": id_,
        "url": f"https://notion.so/{id_}",
        "properties": {
            "Nome": {
                "type": "title",
                "title": [{"plain_text": nome}],
            }
        },
    }


def _resposta_consulta(resultados: list[dict] | None = None) -> dict:
    return {
        "results": resultados or [],
        "has_more": False,
        "next_cursor": None,
    }


def test_item_coletado_campos_basicos():
    item = ItemColetado(nome="test.py", tipo_fonte="arquivos", origem="test.py")
    assert item.metadados == {}
    assert item.origem == "test.py"


def test_fonte_arquivos_coleta_recursivamente_com_origem_relativa(tmp_path: Path):
    (tmp_path / "a.txt").write_text("conteúdo A")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "b.py").write_text("print('b')")

    itens = list(FonteArquivos(tmp_path).coletar())
    assert [item.origem for item in itens] == ["a.txt", "subdir/b.py"]
    assert itens[0].conteudo == "conteúdo A"
    assert itens[1].metadados["caminho_relativo"] == "subdir/b.py"


def test_fonte_arquivos_pode_limitar_ao_primeiro_nivel(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a")
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "b.txt").write_text("b")
    itens = list(FonteArquivos(tmp_path, recursivo=False).coletar())
    assert [item.nome for item in itens] == ["a.txt"]


def test_fonte_arquivos_filtra_extensao_sem_diferenciar_caixa(tmp_path: Path):
    (tmp_path / "a.TXT").write_text("x")
    (tmp_path / "b.py").write_text("y")
    itens = list(FonteArquivos(tmp_path, extensoes=["txt"]).coletar())
    assert [item.nome for item in itens] == ["a.TXT"]


def test_fonte_arquivos_nao_le_binario_como_texto(tmp_path: Path):
    (tmp_path / "imagem.bin").write_bytes(b"\x00\x01")
    item = list(FonteArquivos(tmp_path).coletar())[0]
    assert item.conteudo == "Arquivo .bin (2 bytes)"


def test_fonte_arquivos_pasta_inexistente():
    assert list(FonteArquivos("/caminho/que/nao/existe").coletar()) == []


def test_fonte_arquivos_valida_configuracao():
    with pytest.raises(ValueError, match="max_caracteres"):
        FonteArquivos(".", max_caracteres=-1)
    with pytest.raises(ValueError, match="extensoes"):
        FonteArquivos(".", extensoes=[""])


class _GitHubFixo:
    def listar_repos(self, usuario: str):
        assert usuario == "felipe"
        return [
            RepoInfo(
                nome="r1",
                nome_completo="felipe/r1",
                descricao="desc",
                linguagem="Python",
                estrelas=1,
            )
        ]


def test_fonte_github_converte_repo_em_item():
    itens = list(FonteGitHub("felipe", github_client=_GitHubFixo()).coletar())
    assert len(itens) == 1
    assert itens[0].nome == "r1"
    assert itens[0].origem == "felipe/r1"
    assert itens[0].metadados["linguagem"] == "Python"


def test_fontes_concretas_implementam_protocolo():
    assert isinstance(FonteArquivos("/tmp"), Fonte)
    assert isinstance(FonteGitHub("user"), Fonte)


def test_propriedades_validam_item_e_limitam_texto():
    props = _propriedades_de_item(
        ItemColetado(
            nome="n" * 2500,
            tipo_fonte="teste",
            conteudo="c" * 2500,
            origem="o" * 2500,
        )
    )
    assert len(props["Nome"]["title"][0]["text"]["content"]) == 2000
    assert len(props["Descrição"]["rich_text"][0]["text"]["content"]) == 2000
    with pytest.raises(ValueError, match="nome"):
        _propriedades_de_item(ItemColetado(nome=" ", tipo_fonte="teste"))


class _FonteFixa:
    def __init__(self, itens: list[ItemColetado]) -> None:
        self._itens = itens

    def coletar(self):
        return iter(self._itens)


@responses.activate
def test_ingerir_cria_pagina_quando_origem_nao_existe():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json=_resposta_consulta(),
        status=200,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/pages",
        json=_pagina_resposta("p1"),
        status=200,
    )
    fonte = _FonteFixa([ItemColetado(nome="item1", tipo_fonte="teste", origem="o1")])
    resultado = ingerir(
        fonte,
        client=NotionClient(token=TOKEN),
        database_id=DB,
    )
    assert resultado.criados == 1
    assert resultado.atualizados == 0
    assert resultado.erros == 0


@responses.activate
def test_ingerir_atualiza_pagina_existente_por_origem():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json=_resposta_consulta([_pagina_resposta("existente")]),
        status=200,
    )
    responses.add(
        responses.PATCH,
        f"{NOTION_BASE_URL}/pages/existente",
        json=_pagina_resposta("existente"),
        status=200,
    )
    fonte = _FonteFixa([ItemColetado(nome="item1", tipo_fonte="teste", origem="o1")])
    resultado = ingerir(
        fonte,
        client=NotionClient(token=TOKEN),
        database_id=DB,
    )
    assert resultado.criados == 0
    assert resultado.atualizados == 1


@responses.activate
def test_ingerir_conta_erros_sem_interromper_lote():
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json={"message": "bad request"},
        status=400,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/databases/{DB}/query",
        json=_resposta_consulta(),
        status=200,
    )
    responses.add(
        responses.POST,
        f"{NOTION_BASE_URL}/pages",
        json=_pagina_resposta("p2"),
        status=200,
    )
    fonte = _FonteFixa(
        [
            ItemColetado(nome="falha", tipo_fonte="teste", origem="o1"),
            ItemColetado(nome="ok", tipo_fonte="teste", origem="o2"),
        ]
    )
    resultado = ingerir(
        fonte,
        client=NotionClient(token=TOKEN),
        database_id=DB,
    )
    assert resultado.criados == 1
    assert resultado.erros == 1
    assert resultado.itens_processados == 2


def test_ingerir_item_invalido_e_contabilizado():
    fonte = _FonteFixa([ItemColetado(nome="", tipo_fonte="teste")])
    resultado = ingerir(
        fonte,
        client=NotionClient(token=TOKEN),
        database_id=DB,
    )
    assert resultado.erros == 1
    assert resultado.itens_processados == 1


def test_ingerir_sem_database_id_levanta_erro(monkeypatch):
    monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
    with pytest.raises(ValueError, match="database_id"):
        ingerir(
            _FonteFixa([]),
            client=NotionClient(token=TOKEN),
        )


def test_ingerir_fonte_vazia():
    resultado = ingerir(
        _FonteFixa([]),
        client=NotionClient(token=TOKEN),
        database_id=DB,
    )
    assert resultado == resultado.__class__()
