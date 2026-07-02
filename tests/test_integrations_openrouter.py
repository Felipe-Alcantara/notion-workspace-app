"""Testes da integração OpenRouter (``integrations.openrouter``).

Catálogo de modelos, cache, parsing e provedor — tudo mockado com ``responses``,
sem rede nem chave real.
"""

from __future__ import annotations

import json
import os
import time

import pytest
import responses
from integrations.openrouter import (
    CHAT_URL,
    MODELS_URL,
    CatalogoErro,
    Modelo,
    ProvedorErro,
    ProvedorIA,
    ProvedorOpenRouter,
    _parse_modelos,
    carregar_modelos,
    empresas,
    modelos_da_empresa,
)

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

_PAYLOAD_MODELOS = {
    "data": [
        {
            "id": "openai/gpt-4.1-nano",
            "name": "GPT-4.1 Nano",
            "pricing": {"completion": "0.0004"},
        },
        {
            "id": "openai/gpt-4.1",
            "name": "GPT-4.1",
            "pricing": {"completion": "0.008"},
        },
        {
            "id": "anthropic/claude-sonnet-4",
            "name": "Claude Sonnet 4",
            "pricing": {"completion": "0.015"},
        },
        {
            "id": "malformado-sem-barra",
            "name": "Ignora",
        },
    ]
}


@pytest.fixture(autouse=True)
def _limpar_cache(tmp_path, monkeypatch):
    """Aponta o cache para um diretório temporário em cada teste."""
    cache = tmp_path / ".openrouter_models_cache.json"
    import integrations.openrouter as mod

    monkeypatch.setattr(mod, "_CACHE_PATH", cache)
    yield


# ---------------------------------------------------------------------------
# Parsing de modelos
# ---------------------------------------------------------------------------


def test_parse_modelos_ignora_malformados():
    modelos = _parse_modelos(_PAYLOAD_MODELOS)
    ids = [m.id for m in modelos]
    assert "malformado-sem-barra" not in ids
    assert len(modelos) == 3


def test_parse_modelos_extrai_empresa_e_preco():
    modelos = _parse_modelos(_PAYLOAD_MODELOS)
    gpt = next(m for m in modelos if m.id == "openai/gpt-4.1")
    assert gpt.empresa == "openai"
    assert gpt.nome == "GPT-4.1"
    assert gpt.preco_saida == pytest.approx(0.008)


def test_parse_modelos_preco_ausente_vira_zero():
    payload = {"data": [{"id": "x/y", "name": "Y"}]}
    modelos = _parse_modelos(payload)
    assert modelos[0].preco_saida == 0.0


# ---------------------------------------------------------------------------
# Catálogo (carregar_modelos, cache)
# ---------------------------------------------------------------------------


@responses.activate
def test_carregar_modelos_da_rede_e_grava_cache(tmp_path, monkeypatch):
    responses.add(responses.GET, MODELS_URL, json=_PAYLOAD_MODELOS, status=200)

    modelos = carregar_modelos(timeout=5.0)
    assert len(modelos) == 3

    import integrations.openrouter as mod

    assert mod._CACHE_PATH.exists()


@responses.activate
def test_carregar_modelos_usa_cache_fresco(tmp_path, monkeypatch):
    """Se o cache é fresco (< 24 h), não chama a rede."""
    import integrations.openrouter as mod

    cache_data = {"modelos": [Modelo("a/b", "a", "B", 0.01).__dict__]}
    mod._CACHE_PATH.write_text(json.dumps(cache_data), encoding="utf-8")

    modelos = carregar_modelos()
    assert len(modelos) == 1
    assert modelos[0].id == "a/b"
    assert len(responses.calls) == 0  # não chamou a rede


@responses.activate
def test_carregar_modelos_fallback_cache_vencido(tmp_path, monkeypatch):
    """Se a rede falhar mas houver cache vencido, usa o cache."""
    import integrations.openrouter as mod

    cache_data = {"modelos": [Modelo("a/b", "a", "B", 0.01).__dict__]}
    mod._CACHE_PATH.write_text(json.dumps(cache_data), encoding="utf-8")
    # Força cache vencido (mtime antigo).
    vencido = time.time() - (25 * 60 * 60)
    os.utime(mod._CACHE_PATH, (vencido, vencido))

    responses.add(responses.GET, MODELS_URL, body=ConnectionError("sem rede"))

    modelos = carregar_modelos()
    assert len(modelos) == 1


@responses.activate
def test_carregar_modelos_sem_rede_sem_cache_levanta():
    responses.add(responses.GET, MODELS_URL, body=ConnectionError("sem rede"))

    with pytest.raises(CatalogoErro):
        carregar_modelos()


# ---------------------------------------------------------------------------
# Agrupamento (empresas, modelos_da_empresa)
# ---------------------------------------------------------------------------


def test_empresas_distintas_ordenadas():
    modelos = _parse_modelos(_PAYLOAD_MODELOS)
    assert empresas(modelos) == ["anthropic", "openai"]


def test_modelos_da_empresa_ordenados_por_preco_desc():
    modelos = _parse_modelos(_PAYLOAD_MODELOS)
    openai = modelos_da_empresa(modelos, "openai")
    assert openai[0].id == "openai/gpt-4.1"  # mais caro primeiro
    assert openai[1].id == "openai/gpt-4.1-nano"


# ---------------------------------------------------------------------------
# ProvedorIA (protocolo)
# ---------------------------------------------------------------------------


def test_provedor_openrouter_implementa_protocolo():
    assert isinstance(ProvedorOpenRouter(), ProvedorIA)


# ---------------------------------------------------------------------------
# ProvedorOpenRouter.completar (mockado)
# ---------------------------------------------------------------------------


@responses.activate
def test_completar_retorna_texto(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-fake")

    responses.add(
        responses.POST,
        CHAT_URL,
        json={
            "choices": [{"message": {"content": "Resposta do modelo."}}],
        },
        status=200,
    )

    provedor = ProvedorOpenRouter(modelo_padrao="openai/gpt-4.1-nano")
    resultado = provedor.completar("Olá!")
    assert resultado == "Resposta do modelo."


@responses.activate
def test_completar_usa_modelo_informado(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-fake")

    responses.add(
        responses.POST,
        CHAT_URL,
        json={
            "choices": [{"message": {"content": "ok"}}],
        },
        status=200,
    )

    provedor = ProvedorOpenRouter()
    provedor.completar("Olá!", modelo="anthropic/claude-sonnet-4")

    corpo = json.loads(responses.calls[0].request.body)
    assert corpo["model"] == "anthropic/claude-sonnet-4"


@responses.activate
def test_completar_erro_http_levanta(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-fake")
    responses.add(responses.POST, CHAT_URL, json={"error": "nope"}, status=401)

    provedor = ProvedorOpenRouter()
    with pytest.raises(ProvedorErro, match="HTTP 401"):
        provedor.completar("Olá!")


def test_completar_sem_chave_levanta(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    provedor = ProvedorOpenRouter()
    with pytest.raises(ProvedorErro, match="OPENROUTER_API_KEY"):
        provedor.completar("Olá!")


@responses.activate
def test_completar_resposta_malformada_levanta(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key-fake")
    responses.add(responses.POST, CHAT_URL, json={"choices": []}, status=200)

    provedor = ProvedorOpenRouter()
    with pytest.raises(ProvedorErro, match="sem choices"):
        provedor.completar("Olá!")
