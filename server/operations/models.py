"""Modelos de **estado operacional** — não são conteúdo, são controle de execução.

O conteúdo (tarefas, páginas) vive no Notion, a fonte da verdade. O SQLite local
guarda só o que faz o servidor operar de forma confiável: o registro de jobs
(sincronizações, ingestões) e locks para evitar processamento concorrente.

Modelos enxutos de propósito — o Agente Integrações / Otimização os expande
conforme as filas e a idempotência (Fases 3+) exigirem.
"""

from __future__ import annotations

from django.db import models


class Job(models.Model):
    """Um trabalho operacional (ex.: sincronizar GitHub, ingerir uma pasta)."""

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        RODANDO = "rodando", "Rodando"
        CONCLUIDO = "concluido", "Concluído"
        FALHOU = "falhou", "Falhou"

    tipo = models.CharField(max_length=64, help_text="Categoria do job, ex.: 'sync_github'.")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDENTE)
    payload = models.JSONField(default=dict, blank=True, help_text="Parâmetros do job.")
    resultado = models.JSONField(null=True, blank=True, help_text="Saída ou erro do job.")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-criado_em",)
        indexes = [models.Index(fields=["status", "tipo"])]

    def __str__(self) -> str:
        return f"Job#{self.pk} {self.tipo} [{self.status}]"


class Lock(models.Model):
    """Lock nomeado para serializar operações que não podem rodar em paralelo."""

    nome = models.CharField(max_length=128, unique=True)
    dono = models.CharField(max_length=128, blank=True, help_text="Quem detém o lock.")
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Lock({self.nome})"
