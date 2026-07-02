"""Roteamento raiz do servidor.

Delega ``/api/`` para o app ``api`` (borda HTTP) e serve o front web em ``/``.
"""

from __future__ import annotations

from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="tarefas.html"), name="home"),
    path("api/", include("api.urls")),
]
