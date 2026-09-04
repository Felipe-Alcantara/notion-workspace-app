"""Roteamento raiz do servidor.

Delega ``/api/`` para o app ``api`` (borda HTTP) e serve o front web em ``/``.
"""

from __future__ import annotations

from pathlib import Path

from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import TemplateView

_SERVER_DIR = Path(__file__).resolve().parent.parent
_RAIZ_PACOTE = _SERVER_DIR.parent
_BUNDLE_INDEX = _SERVER_DIR / "static" / "frontend" / "index.html"


def home(request):
    """Serve a SPA empacotada ou o front legado usado no desenvolvimento."""

    # O checkout mantém ``front/`` para Vite e testes do modo de desenvolvimento.
    # O wheel não leva essa árvore; nesse caso o bundle gerado vira a entrada única.
    if _BUNDLE_INDEX.exists() and not (_RAIZ_PACOTE / "front" / "package.json").exists():
        return HttpResponse(_BUNDLE_INDEX.read_text(encoding="utf-8"), content_type="text/html")
    return TemplateView.as_view(template_name="tarefas.html")(request)


urlpatterns = [
    path("", home, name="home"),
    path("api/", include("api.urls")),
]
