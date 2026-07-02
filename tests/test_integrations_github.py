"""Testes do adaptador GitHub, sem rede real."""

from __future__ import annotations

import pytest
import requests
import responses
from integrations.github import (
    GITHUB_API_BASE,
    GitHubAPIError,
    GitHubClient,
    GitHubConnectionError,
    RepoInfo,
    _repo_de_resposta,
)


def _repo_json(
    nome: str = "meu-repo",
    full_name: str = "user/meu-repo",
    **extras,
) -> dict:
    owner = full_name.split("/", 1)[0]
    base = {
        "name": nome,
        "full_name": full_name,
        "owner": {"login": owner},
        "description": "Um repo de teste",
        "html_url": f"https://github.com/{full_name}",
        "url": f"https://api.github.com/repos/{full_name}",
        "homepage": "https://example.com",
        "language": "Python",
        "topics": ["notion", "automação"],
        "stargazers_count": 42,
        "forks_count": 5,
        "private": False,
        "default_branch": "main",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-06-25T10:00:00Z",
    }
    base.update(extras)
    return base


def test_repo_de_resposta_converte_todos_os_campos():
    info = _repo_de_resposta(
        _repo_json(
            open_issues_count=7,
            watchers_count=9,
            size=128,
            fork=True,
            archived=True,
            license={"spdx_id": "MIT"},
            pushed_at="2026-06-26T00:00:00Z",
        )
    )
    assert isinstance(info, RepoInfo)
    assert info.nome == "meu-repo"
    assert info.nome_completo == "user/meu-repo"
    assert info.homepage == "https://example.com"
    assert info.topicos == ["notion", "automação"]
    assert info.estrelas == 42
    assert info.forks == 5
    assert info.privado is False
    assert info.dono == "user"
    assert info.issues_abertas == 7
    assert info.observadores == 9
    assert info.tamanho_kb == 128
    assert info.fork is True
    assert info.arquivado is True
    assert info.licenca == "MIT"
    assert info.enviado_em == "2026-06-26T00:00:00Z"


def test_repo_de_resposta_normaliza_campos_ausentes():
    info = _repo_de_resposta({"name": "x", "full_name": "u/x", "topics": None})
    assert info.descricao is None
    assert info.topicos == []
    assert info.estrelas == 0
    assert info.homepage is None
    assert info.licenca is None
    assert info.dono is None
    assert info.fork is False
    assert info.arquivado is False
    assert info.issues_abertas == 0


def test_client_valida_configuracao():
    with pytest.raises(ValueError, match="max_retries"):
        GitHubClient(max_retries=-1)
    with pytest.raises(ValueError, match="timeout"):
        GitHubClient(timeout=0)
    with pytest.raises(ValueError, match="max_repos"):
        GitHubClient(max_repos=0)


def test_headers_so_expoem_token_quando_configurado():
    assert "Authorization" not in GitHubClient(token="")._headers()
    headers = GitHubClient(token="ghp_test123")._headers()
    assert headers["Authorization"] == "Bearer ghp_test123"


@responses.activate
def test_listar_repos_publicos_sem_token():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/users/felipe/repos",
        json=[
            _repo_json("repo-a", "felipe/repo-a"),
            _repo_json("repo-b", "felipe/repo-b"),
        ],
        status=200,
    )
    repos = GitHubClient(token="", max_retries=0).listar_repos("felipe")
    assert [repo.nome for repo in repos] == ["repo-a", "repo-b"]
    assert len(responses.calls) == 1


@responses.activate
def test_listar_repos_inclui_privados_do_usuario_autenticado_e_deduplica():
    publico = _repo_json("publico", "felipe/publico")
    privado = _repo_json(
        "privado",
        "felipe/privado",
        private=True,
        updated_at="2026-06-26T10:00:00Z",
    )
    terceiro = _repo_json("terceiro", "outra/terceiro", private=True)
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/users/felipe/repos",
        json=[publico],
        status=200,
    )
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/user",
        json={"login": "Felipe"},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/user/repos",
        json=[publico, privado, terceiro],
        status=200,
    )

    repos = GitHubClient(token="ghp_test", max_retries=0).listar_repos("felipe")
    assert [repo.nome for repo in repos] == ["privado", "publico"]
    assert repos[0].privado is True


@responses.activate
def test_listar_repos_nao_busca_privados_de_outro_usuario():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/users/alvo/repos",
        json=[],
        status=200,
    )
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/user",
        json={"login": "autenticado"},
        status=200,
    )
    repos = GitHubClient(token="ghp_test", max_retries=0).listar_repos("alvo")
    assert repos == []
    assert len(responses.calls) == 2


@responses.activate
def test_listar_repos_paginacao_e_limite_operacional():
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/users/felipe/repos",
        json=[_repo_json("r1", "felipe/r1"), _repo_json("r2", "felipe/r2")],
        status=200,
    )
    responses.add(
        responses.GET,
        f"{GITHUB_API_BASE}/users/felipe/repos",
        json=[_repo_json("r3", "felipe/r3")],
        status=200,
    )
    client = GitHubClient(token="", max_retries=0, max_repos=3)
    repos = client._get_paginado("/users/felipe/repos", por_pagina=2)
    assert len(repos) == 3


@responses.activate
def test_detalhar_repo_enriquece_linguagens_e_readme():
    base = f"{GITHUB_API_BASE}/repos/felipe/notion"
    responses.add(
        responses.GET,
        base,
        json=_repo_json("notion", "felipe/notion"),
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base}/languages",
        json={"Python": 1000, "HTML": 250},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{base}/readme",
        body="# Projeto\nDocumentação",
        status=200,
        content_type="text/plain",
    )
    info = GitHubClient(token="", max_retries=0).detalhar_repo("felipe/notion")
    assert info.linguagens == {"Python": 1000, "HTML": 250}
    assert info.readme == "# Projeto\nDocumentação"


@responses.activate
def test_detalhar_repo_aceita_readme_ausente():
    base = f"{GITHUB_API_BASE}/repos/felipe/notion"
    responses.add(
        responses.GET,
        base,
        json=_repo_json("notion", "felipe/notion"),
        status=200,
    )
    responses.add(responses.GET, f"{base}/languages", json={}, status=200)
    responses.add(responses.GET, f"{base}/readme", json={"message": "Not Found"}, status=404)
    info = GitHubClient(token="", max_retries=0).detalhar_repo("felipe/notion")
    assert info.readme is None


@responses.activate
def test_retry_em_429_respeita_retry_after():
    url = f"{GITHUB_API_BASE}/repos/u/r"
    responses.add(
        responses.GET,
        url,
        json={"message": "rate limit"},
        status=429,
        headers={"Retry-After": "0"},
    )
    responses.add(responses.GET, url, json=_repo_json("r", "u/r"), status=200)
    responses.add(responses.GET, f"{url}/languages", json={}, status=200)
    responses.add(responses.GET, f"{url}/readme", status=404)
    info = GitHubClient(token="", max_retries=1, backoff_base=0).detalhar_repo("u/r")
    assert info.nome == "r"
    assert len(responses.calls) == 4


@responses.activate
def test_retry_em_erro_de_rede(monkeypatch):
    chamadas = 0
    resposta = requests.Response()
    resposta.status_code = 200
    resposta._content = b'{"name":"r","full_name":"u/r"}'

    def request_mock(**kwargs):
        nonlocal chamadas
        chamadas += 1
        if chamadas == 1:
            raise requests.ConnectionError("offline")
        return resposta

    monkeypatch.setattr(requests, "request", request_mock)
    resultado = GitHubClient(token="", max_retries=1, backoff_base=0)._request_json(
        method="GET",
        path="/repos/u/r",
    )
    assert resultado["name"] == "r"
    assert chamadas == 2


def test_erro_de_rede_esgotado_usa_excecao_propria(monkeypatch):
    def request_mock(**kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr(requests, "request", request_mock)
    with pytest.raises(GitHubConnectionError, match="timeout"):
        GitHubClient(token="", max_retries=1, backoff_base=0)._request_json(
            method="GET",
            path="/repos/u/r",
        )


@responses.activate
def test_403_de_permissao_nao_faz_retry():
    url = f"{GITHUB_API_BASE}/repos/u/r"
    responses.add(
        responses.GET,
        url,
        json={"message": "Resource not accessible by personal access token"},
        status=403,
    )
    with pytest.raises(GitHubAPIError) as exc:
        GitHubClient(token="ghp_test", max_retries=3, backoff_base=0)._request_json(
            method="GET",
            path="/repos/u/r",
        )
    assert exc.value.status_code == 403
    assert len(responses.calls) == 1


@responses.activate
def test_rate_limit_expoe_headers_operacionais():
    url = f"{GITHUB_API_BASE}/repos/u/r"
    responses.add(
        responses.GET,
        url,
        json={"message": "rate limit exceeded"},
        status=403,
        headers={
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "12345",
        },
    )
    with pytest.raises(GitHubAPIError) as exc:
        GitHubClient(token="", max_retries=0)._request_json(
            method="GET",
            path="/repos/u/r",
        )
    assert exc.value.rate_limit is not None
    assert exc.value.rate_limit.restante == 0
    assert exc.value.rate_limit.reset_em == 12345


@responses.activate
def test_retry_esgotado_em_500():
    url = f"{GITHUB_API_BASE}/repos/u/r"
    responses.add(responses.GET, url, json={"message": "error"}, status=500)
    responses.add(responses.GET, url, json={"message": "error"}, status=500)
    with pytest.raises(GitHubAPIError, match="500"):
        GitHubClient(token="", max_retries=1, backoff_base=0)._request_json(
            method="GET",
            path="/repos/u/r",
        )


@pytest.mark.parametrize("usuario", ["", "../admin", "nome com espaço", "a" * 40])
def test_listar_repos_valida_usuario_antes_do_http(usuario):
    with pytest.raises(ValueError, match="usuario"):
        GitHubClient(token="").listar_repos(usuario)


@pytest.mark.parametrize("repo", ["", "apenas-owner", "a/b/c", "../repo", "a/repo espaço"])
def test_detalhar_repo_valida_formato(repo):
    with pytest.raises(ValueError, match="repo_completo"):
        GitHubClient(token="").detalhar_repo(repo)


def test_calcular_espera_retry_after_e_backoff():
    client = GitHubClient(token="", backoff_base=2)
    com_header = type("R", (), {"headers": {"Retry-After": "3"}})()
    sem_header = type("R", (), {"headers": {}})()
    assert client._calcular_espera(com_header, 0) == 3
    assert client._calcular_espera(sem_header, 2) == 8
