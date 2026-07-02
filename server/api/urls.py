"""Rotas sob ``/api/``.

Health check (Infra) + rotas de tarefas (Backend), seguindo o esboço da Fase 2 em
``docs/PLANO.md`` / o contrato do Agente 0.
"""

from __future__ import annotations

from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("tarefas", views.tarefas, name="tarefas"),
    path("tarefas/<str:task_id>", views.tarefa_detalhe, name="tarefa-detalhe"),
    path("opcoes", views.opcoes, name="opcoes"),
    path("database-atual", views.database_atual, name="database-atual"),
    path("databases", views.databases, name="databases"),
    path("databases/<str:database_id>", views.database_detalhe, name="database-detalhe"),
]
