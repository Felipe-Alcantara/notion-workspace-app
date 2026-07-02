/**
 * Front-end das Automações do Notion.
 *
 * Consome as rotas REST do Backend (docs/CONTRATOS.md §2):
 *   GET    /api/tarefas[?status=<nome>]
 *   POST   /api/tarefas
 *   PATCH  /api/tarefas/<id>
 *
 * Sem regra de negócio — só apresentação e delegação à API.
 */

"use strict";

// ── Elementos do DOM ──────────────────────────────────────────

const elFiltro = document.getElementById("filtro-status");
const elBtnRecarregar = document.getElementById("btn-recarregar");
const elBtnAbrirForm = document.getElementById("btn-abrir-form");
const elFormCriar = document.getElementById("form-criar");
const elFormTarefa = document.getElementById("form-tarefa");
const elBtnCancelar = document.getElementById("btn-cancelar");
const elInputNome = document.getElementById("input-nome");
const elInputStatus = document.getElementById("input-status");
const elInputPrazo = document.getElementById("input-prazo");
const elCarregando = document.getElementById("estado-carregando");
const elErro = document.getElementById("estado-erro");
const elErroMsg = document.getElementById("erro-mensagem");
const elBtnTentarNovamente = document.getElementById("btn-tentar-novamente");
const elVazio = document.getElementById("estado-vazio");
const elLista = document.getElementById("lista-tarefas");
const elMensagemOperacao = document.getElementById("mensagem-operacao");
const elModal = document.getElementById("modal-status");
const elFormStatus = document.getElementById("form-status");
const elModalNome = document.getElementById("modal-tarefa-nome");
const elModalNovoStatus = document.getElementById("modal-novo-status");
const elBtnConfirmar = document.getElementById("btn-confirmar-status");
const elBtnFecharModal = document.getElementById("btn-fechar-modal");

// ── Estado ────────────────────────────────────────────────────

let tarefaParaMover = null;
let statusConhecidos = new Set();
let elementoFocoAnterior = null;

// ── API ───────────────────────────────────────────────────────

const API_BASE = "/api";

async function apiGet(caminho) {
  const resp = await fetch(`${API_BASE}${caminho}`);
  const dados = await resp.json();
  if (!resp.ok) {
    throw new Error(
      (dados.erro && dados.erro.mensagem) || `Erro ${resp.status}`
    );
  }
  return dados;
}

async function apiPost(caminho, corpo) {
  const resp = await fetch(`${API_BASE}${caminho}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  const dados = await resp.json();
  if (!resp.ok) {
    throw new Error(
      (dados.erro && dados.erro.mensagem) || `Erro ${resp.status}`
    );
  }
  return dados;
}

async function apiPatch(caminho, corpo) {
  const resp = await fetch(`${API_BASE}${caminho}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  const dados = await resp.json();
  if (!resp.ok) {
    throw new Error(
      (dados.erro && dados.erro.mensagem) || `Erro ${resp.status}`
    );
  }
  return dados;
}

// ── Renderização ──────────────────────────────────────────────

function mostrarEstado(estado) {
  elCarregando.hidden = estado !== "carregando";
  elErro.hidden = estado !== "erro";
  elVazio.hidden = estado !== "vazio";
  elLista.hidden = estado !== "lista";
}

function mostrarMensagem(mensagem, tipo = "sucesso") {
  elMensagemOperacao.textContent = mensagem;
  elMensagemOperacao.dataset.tipo = tipo;
  elMensagemOperacao.hidden = false;
}

function ocultarMensagem() {
  elMensagemOperacao.hidden = true;
  elMensagemOperacao.textContent = "";
  delete elMensagemOperacao.dataset.tipo;
}

function renderizarTarefa(tarefa) {
  const li = document.createElement("li");
  li.className = "tarefa-item";

  const info = document.createElement("div");
  info.className = "tarefa-info";

  const nome = document.createElement("div");
  nome.className = "tarefa-nome";
  if (tarefa.url) {
    const link = document.createElement("a");
    link.href = tarefa.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = tarefa.nome;
    nome.appendChild(link);
  } else {
    nome.textContent = tarefa.nome;
  }
  info.appendChild(nome);

  const meta = document.createElement("div");
  meta.className = "tarefa-meta";

  if (tarefa.status) {
    const badge = document.createElement("span");
    badge.className = "badge-status";
    badge.textContent = tarefa.status;
    meta.appendChild(badge);
  }

  if (tarefa.prazo) {
    const prazo = document.createElement("span");
    prazo.textContent = tarefa.prazo;
    meta.appendChild(prazo);
  }

  if (meta.childNodes.length > 0) {
    info.appendChild(meta);
  }

  li.appendChild(info);

  const acoes = document.createElement("div");
  acoes.className = "tarefa-acoes";

  const btnMover = document.createElement("button");
  btnMover.type = "button";
  btnMover.className = "btn btn-secondary btn-small";
  btnMover.textContent = "Mover / concluir";
  btnMover.setAttribute("aria-label", `Mover ou concluir: ${tarefa.nome}`);
  btnMover.addEventListener("click", () => abrirModalStatus(tarefa));
  acoes.appendChild(btnMover);

  li.appendChild(acoes);
  return li;
}

function atualizarFiltroStatus() {
  const valorAtual = elFiltro.value;
  const opcoes = Array.from(statusConhecidos).sort();

  // Limpa tudo exceto a opção "Todos"
  while (elFiltro.options.length > 1) {
    elFiltro.remove(1);
  }

  for (const s of opcoes) {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    elFiltro.appendChild(opt);
  }

  // Restaura seleção se ainda existir
  if (statusConhecidos.has(valorAtual)) {
    elFiltro.value = valorAtual;
  }
}

// ── Ações ─────────────────────────────────────────────────────

async function carregarTarefas() {
  mostrarEstado("carregando");

  try {
    const filtro = elFiltro.value;
    const qs = filtro ? `?status=${encodeURIComponent(filtro)}` : "";
    const dados = await apiGet(`/tarefas${qs}`);
    const tarefas = dados.tarefas || [];

    // Coleta status conhecidos (de todas as cargas, acumulativo)
    for (const t of tarefas) {
      if (t.status) {
        statusConhecidos.add(t.status);
      }
    }
    atualizarFiltroStatus();

    if (tarefas.length === 0) {
      mostrarEstado("vazio");
      return;
    }

    elLista.innerHTML = "";
    for (const t of tarefas) {
      elLista.appendChild(renderizarTarefa(t));
    }
    mostrarEstado("lista");
  } catch (err) {
    elErroMsg.textContent = err.message || "Erro ao carregar tarefas.";
    mostrarEstado("erro");
  }
}

async function criarTarefa(ev) {
  ev.preventDefault();
  ocultarMensagem();
  const nome = elInputNome.value.trim();
  if (!nome) return;

  const corpo = { nome: nome };
  const status = elInputStatus.value.trim();
  const prazo = elInputPrazo.value;
  if (status) corpo.status = status;
  if (prazo) corpo.prazo = prazo;

  const btnSubmit = elFormTarefa.querySelector('button[type="submit"]');
  btnSubmit.disabled = true;
  btnSubmit.textContent = "Criando...";

  try {
    await apiPost("/tarefas", corpo);
    elFormTarefa.reset();
    fecharFormCriar();
    await carregarTarefas();
    mostrarMensagem("Tarefa criada com sucesso.");
  } catch (err) {
    mostrarMensagem(`Erro ao criar tarefa: ${err.message}`, "erro");
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.textContent = "Criar";
  }
}

function abrirModalStatus(tarefa) {
  elementoFocoAnterior = document.activeElement;
  tarefaParaMover = tarefa;
  elModalNome.textContent = tarefa.nome;
  elModalNovoStatus.value = tarefa.status || "";
  elModal.hidden = false;
  elModalNovoStatus.focus();
}

function fecharModal() {
  elModal.hidden = true;
  tarefaParaMover = null;
  if (elementoFocoAnterior instanceof HTMLElement) {
    elementoFocoAnterior.focus();
  }
  elementoFocoAnterior = null;
}

async function confirmarMoverStatus(ev) {
  ev.preventDefault();
  ocultarMensagem();
  if (!tarefaParaMover) return;
  const novoStatus = elModalNovoStatus.value.trim();
  if (!novoStatus) return;

  elBtnConfirmar.disabled = true;
  elBtnConfirmar.textContent = "Movendo...";

  try {
    await apiPatch(`/tarefas/${tarefaParaMover.id}`, { status: novoStatus });
    fecharModal();
    await carregarTarefas();
    mostrarMensagem("Etapa atualizada com sucesso.");
  } catch (err) {
    mostrarMensagem(`Erro ao atualizar status: ${err.message}`, "erro");
  } finally {
    elBtnConfirmar.disabled = false;
    elBtnConfirmar.textContent = "Confirmar";
  }
}

function abrirFormCriar() {
  ocultarMensagem();
  elFormCriar.hidden = false;
  elInputNome.focus();
}

function fecharFormCriar() {
  elFormCriar.hidden = true;
  elFormTarefa.reset();
}

// ── Event listeners ───────────────────────────────────────────

elBtnAbrirForm.addEventListener("click", abrirFormCriar);
elBtnCancelar.addEventListener("click", fecharFormCriar);
elFormTarefa.addEventListener("submit", criarTarefa);
elFiltro.addEventListener("change", carregarTarefas);
elBtnRecarregar.addEventListener("click", carregarTarefas);
elBtnTentarNovamente.addEventListener("click", carregarTarefas);
elFormStatus.addEventListener("submit", confirmarMoverStatus);
elBtnFecharModal.addEventListener("click", fecharModal);

// Fechar modal clicando fora
elModal.addEventListener("click", (ev) => {
  if (ev.target === elModal) fecharModal();
});

// Fechar modal com Escape
document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") {
    if (!elModal.hidden) fecharModal();
    if (!elFormCriar.hidden) fecharFormCriar();
  }
});

// ── Inicialização ─────────────────────────────────────────────

carregarTarefas();
