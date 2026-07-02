"""Registro do app ``operations`` (estado operacional em SQLite)."""

from __future__ import annotations

from django.apps import AppConfig


class OperationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "operations"
