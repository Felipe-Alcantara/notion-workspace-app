"""Testes do despacho de ações do menu em terminais dedicados."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path

from rich.console import Console

_START_APP = Path(__file__).resolve().parents[1] / "start_app.py"
_SPEC = importlib.util.spec_from_file_location("start_app", _START_APP)
assert _SPEC and _SPEC.loader
start_app = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(start_app)


def test_comando_acao_reabre_start_app_com_acao():
    comando = start_app._comando_acao("servidor")

    assert comando[0] == start_app._executavel_projeto()
    assert comando[1] == str(start_app.Path(start_app.__file__).resolve())
    assert comando[2:] == ["--action", "servidor"]


def test_reexecuta_no_python_do_projeto_quando_venv_difere(monkeypatch):
    chamadas = []
    monkeypatch.setattr(start_app, "_executavel_projeto", lambda: "/tmp/projeto/.venv/bin/python")
    monkeypatch.setattr(start_app.sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(
        start_app.os,
        "execv",
        lambda executavel, argv: chamadas.append((executavel, argv)),
    )

    start_app._reexecutar_no_python_do_projeto(["--action", "tudo"])

    assert chamadas == [
        (
            "/tmp/projeto/.venv/bin/python",
            [
                "/tmp/projeto/.venv/bin/python",
                str(start_app.Path(start_app.__file__).resolve()),
                "--action",
                "tudo",
            ],
        )
    ]


def test_reexecutar_no_python_do_projeto_nao_faz_nada_quando_ja_esta_no_mesmo(monkeypatch):
    monkeypatch.setattr(start_app, "_executavel_projeto", lambda: "/usr/bin/python3")
    monkeypatch.setattr(start_app.sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(
        start_app.os,
        "execv",
        lambda *_args: (_ for _ in ()).throw(AssertionError("não deveria reexecutar")),
    )

    start_app._reexecutar_no_python_do_projeto(["status"])


def test_terminal_linux_prefere_terminal_configurado(monkeypatch):
    monkeypatch.setenv("TERMINAL", "terminal-personalizado --nova-janela")
    monkeypatch.setattr(
        start_app.shutil,
        "which",
        lambda nome: f"/usr/bin/{nome}" if nome == "terminal-personalizado" else None,
    )

    comando = start_app._comando_terminal_linux(["python", "app.py"], "Minha ação")

    assert comando == [
        "/usr/bin/terminal-personalizado",
        "--nova-janela",
        "-e",
        "python",
        "app.py",
    ]


def test_terminal_linux_faz_fallback_para_konsole(monkeypatch):
    monkeypatch.delenv("TERMINAL", raising=False)
    monkeypatch.setattr(
        start_app.shutil,
        "which",
        lambda nome: "/usr/bin/konsole" if nome == "konsole" else None,
    )

    comando = start_app._comando_terminal_linux(["python", "app.py"], "Status")

    assert comando == [
        "/usr/bin/konsole",
        "--separate",
        "-p",
        "tabtitle=Status",
        "-e",
        "python",
        "app.py",
    ]


def test_abrir_terminal_linux_inicia_processo_independente(monkeypatch):
    chamadas = []
    monkeypatch.setattr(start_app.sys, "platform", "linux")
    monkeypatch.setattr(
        start_app,
        "_comando_terminal_linux",
        lambda comando, titulo: ["terminal", "--", *comando],
    )
    monkeypatch.setattr(
        start_app.subprocess,
        "Popen",
        lambda comando, **kwargs: chamadas.append((comando, kwargs)),
    )

    abriu, mensagem = start_app._abrir_terminal_dedicado("status", "Status")

    assert abriu is True
    assert "Status" in mensagem
    comando, kwargs = chamadas[0]
    assert comando[:2] == ["terminal", "--"]
    assert comando[-2:] == ["--action", "status"]
    assert kwargs["cwd"] == start_app.RAIZ
    assert kwargs["start_new_session"] is True


def test_abrir_terminal_informa_quando_nao_ha_emulador(monkeypatch):
    monkeypatch.setattr(start_app.sys, "platform", "linux")
    monkeypatch.setattr(start_app, "_comando_terminal_linux", lambda comando, titulo: None)
    monkeypatch.setattr(
        start_app.subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("não deve abrir processo")),
    )

    abriu, mensagem = start_app._abrir_terminal_dedicado("status", "Status")

    assert abriu is False
    assert "Nenhum emulador de terminal" in mensagem


def test_abrir_terminal_windows_usa_novo_console(monkeypatch):
    chamadas = []
    monkeypatch.setattr(start_app.sys, "platform", "win32")
    monkeypatch.setattr(start_app.subprocess, "CREATE_NEW_CONSOLE", 1234, raising=False)
    monkeypatch.setattr(
        start_app.subprocess,
        "Popen",
        lambda comando, **kwargs: chamadas.append((comando, kwargs)),
    )

    abriu, _ = start_app._abrir_terminal_dedicado("configurar", "Configurar")

    assert abriu is True
    _, kwargs = chamadas[0]
    assert kwargs["creationflags"] == 1234
    assert "start_new_session" not in kwargs


def test_abrir_terminal_trata_falha_do_sistema(monkeypatch):
    monkeypatch.setattr(start_app.sys, "platform", "win32")

    def falhar(*args, **kwargs):
        raise OSError("terminal indisponível")

    monkeypatch.setattr(start_app.subprocess, "Popen", falhar)

    abriu, mensagem = start_app._abrir_terminal_dedicado("status", "Status")

    assert abriu is False
    assert "terminal indisponível" in mensagem


def test_menu_oferece_iniciar_tudo_como_primeira_opcao():
    acoes = start_app._acoes_menu()

    assert next(iter(acoes)) == "tudo"
    assert acoes["tudo"][1] is start_app.acao_iniciar_tudo


def test_categorias_cobrem_todas_as_acoes_sem_orfas():
    acoes = set(start_app._acoes_menu())
    nas_categorias: set[str] = set()
    for _titulo, chaves in start_app._categorias_menu():
        for chave in chaves:
            # Toda chave de categoria existe em _acoes_menu (sem typo/órfã).
            assert chave in acoes
            nas_categorias.add(chave)
    # 'status' fica fora das subtelas (atalho direto); o resto é coberto.
    assert nas_categorias | {"status"} == acoes


def test_acao_qualidade_roda_script_unificado(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        start_app.subprocess,
        "run",
        lambda comando, **kwargs: chamadas.append((comando, kwargs)),
    )
    console = Console(file=io.StringIO(), force_terminal=False)

    start_app.acao_qualidade(console)

    comando, kwargs = chamadas[0]
    assert comando == [start_app.sys.executable, str(start_app.QUALITY_SCRIPT)]
    assert kwargs["cwd"] == start_app.RAIZ
    assert kwargs["check"] is False


def test_instala_extra_servidor_quando_necessario(monkeypatch):
    chamadas = []
    monkeypatch.setattr(start_app, "_django_disponivel", lambda: True)
    monkeypatch.setattr(
        start_app.subprocess,
        "call",
        lambda comando, **kwargs: chamadas.append((comando, kwargs)) or 0,
    )
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._instalar_extra_servidor(console) is True
    comando, kwargs = chamadas[0]
    assert comando[-3:] == ["install", "-e", ".[server]"]
    assert kwargs["cwd"] == start_app.RAIZ


def test_database_compativel_exige_schema_completo():
    database = {
        "properties": {
            "Tarefa": {"type": "title"},
            "Etapa": {"type": "status"},
            "Prazo": {"type": "date"},
        }
    }

    assert start_app._database_compativel(database) is True
    del database["properties"]["Prazo"]
    assert start_app._database_compativel(database) is False


def test_garantir_database_sempre_pergunta_ao_subir(monkeypatch, tmp_path):
    # Mesmo com um database já salvo, "Iniciar tudo" pergunta (com o atual
    # pré-selecionado) — ele NÃO reusa em silêncio.
    import questionary

    capturado = {}

    class Pergunta:
        def ask(self):
            return "db-trocado"

    def fake_select(mensagem, choices, *args, **kwargs):
        capturado["default"] = kwargs.get("default")
        return Pergunta()

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\nNOTION_DATABASE_ID=db-atual\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.setenv(start_app.DATABASE_ENV, "db-atual")
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [("Atual", "db-atual", True, []), ("Outro", "db-trocado", True, [])],
    )
    monkeypatch.setattr(questionary, "select", fake_select)
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._garantir_database_tarefas(console) is True
    # O atual entra pré-selecionado e a troca é gravada.
    assert capturado["default"] == "db-atual"
    assert start_app.os.environ[start_app.DATABASE_ENV] == "db-trocado"


def test_garantir_database_cancelar_mantem_o_atual_e_sobe(monkeypatch, tmp_path):
    # Ao subir, cancelar a escolha mantém o database já salvo e segue (True).
    import questionary

    class Pergunta:
        def ask(self):
            return None  # usuário escolheu "Manter o atual"

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\nNOTION_DATABASE_ID=db-atual\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.setenv(start_app.DATABASE_ENV, "db-atual")
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [("Atual", "db-atual", True, []), ("Outro", "db-outro", True, [])],
    )
    monkeypatch.setattr(questionary, "select", lambda *args, **kwargs: Pergunta())
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._garantir_database_tarefas(console) is True
    assert start_app.os.environ[start_app.DATABASE_ENV] == "db-atual"


def test_garantir_database_pergunta_e_salva_na_primeira_vez(monkeypatch, tmp_path):
    # Sem database salvo, "Iniciar tudo" pergunta (mesmo com um único
    # compatível) e grava a escolha no .env.
    import questionary

    class Pergunta:
        def ask(self):
            return "database-selecionado"

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    # setenv (em vez de delenv) faz o monkeypatch "adotar" a chave: a escrita
    # que a produção faz em os.environ é revertida no teardown, sem vazar para
    # outros testes (ex.: test_api_tarefas, que lê NOTION_DATABASE_ID).
    monkeypatch.setenv(start_app.DATABASE_ENV, "")
    monkeypatch.delenv(start_app.DATABASE_ENV, raising=False)
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [("Tarefas", "database-selecionado", True, [])],
    )
    monkeypatch.setattr(questionary, "select", lambda *args, **kwargs: Pergunta())
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._garantir_database_tarefas(console) is True
    assert "NOTION_DATABASE_ID=database-selecionado" in env_file.read_text()
    assert start_app.os.environ[start_app.DATABASE_ENV] == "database-selecionado"


def test_garantir_database_pede_escolha_quando_ha_mais_de_um(monkeypatch, tmp_path):
    import questionary

    class Pergunta:
        def ask(self):
            return "db-2"

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    # setenv adota a chave para que a escrita da produção em os.environ seja
    # revertida no teardown (ver test_garantir_database_unico_salva_no_env).
    monkeypatch.setenv(start_app.DATABASE_ENV, "")
    monkeypatch.delenv(start_app.DATABASE_ENV, raising=False)
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [("Tarefas", "db-1", True, []), ("Tarefas (1)", "db-2", True, [])],
    )
    monkeypatch.setattr(questionary, "select", lambda *args, **kwargs: Pergunta())
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._garantir_database_tarefas(console) is True
    assert start_app.os.environ[start_app.DATABASE_ENV] == "db-2"


def test_garantir_database_falha_sem_nenhum_compartilhado(monkeypatch, tmp_path):
    # Nenhum database compartilhado com a integração → não há o que escolher.
    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.delenv(start_app.DATABASE_ENV, raising=False)
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(start_app, "_buscar_databases", lambda token: [])
    saida = io.StringIO()
    console = Console(file=saida, force_terminal=False)

    assert start_app._garantir_database_tarefas(console) is False
    assert "Nenhum database compartilhado" in saida.getvalue()


def test_selecionar_database_pergunta_para_trocar_o_atual(monkeypatch, tmp_path):
    # Mesmo com um único database compatível, se já houver um selecionado a
    # opção "Configurar → Escolher database" deve perguntar (para poder trocar),
    # não reusar em silêncio. Marca o atual na lista de escolhas.
    import questionary

    capturado = {}

    class Pergunta:
        def ask(self):
            return "db-novo"

    def fake_select(mensagem, choices, *args, **kwargs):
        capturado["choices"] = choices
        return Pergunta()

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\nNOTION_DATABASE_ID=db-antigo\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.setenv(start_app.DATABASE_ENV, "db-antigo")
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [
            ("Tarefas (atual)", "db-antigo", True, []),
            ("Tarefas nova", "db-novo", True, []),
        ],
    )
    monkeypatch.setattr(questionary, "select", fake_select)
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._selecionar_database_tarefas(console) is True
    assert start_app.os.environ[start_app.DATABASE_ENV] == "db-novo"
    assert "NOTION_DATABASE_ID=db-novo" in env_file.read_text()
    # O database atualmente em uso aparece marcado para o usuário se orientar.
    assert any("[atual]" in str(c.title) for c in capturado["choices"])


def test_selecionar_database_cancelado_mostra_titulo_real_do_atual(monkeypatch, tmp_path):
    import questionary

    class Pergunta:
        def ask(self):
            return None

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\nNOTION_DATABASE_ID=db-atual\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.setenv(start_app.DATABASE_ENV, "db-atual")
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [("Tasks", "db-atual", True, [], ["Tasks"])],
    )
    monkeypatch.setattr(questionary, "select", lambda *args, **kwargs: Pergunta())
    saida = io.StringIO()
    console = Console(file=saida, force_terminal=False)

    assert start_app._selecionar_database_tarefas(console, manter_atual_ao_cancelar=True) is True
    assert "Tasks (db-atual" in saida.getvalue()
    assert "Data source: Tasks" in saida.getvalue()
    assert "URL: https://app.notion.com/p/dbatual" in saida.getvalue()
    assert "Ex.:" not in saida.getvalue()


def test_selecionar_database_lista_todos_com_marca(monkeypatch, tmp_path):
    # Todos os databases aparecem (compatível ✓ e incompatível ⚠), não só os
    # que batem o schema.
    import questionary

    capturado = {}

    class Pergunta:
        def ask(self):
            return "db-ok"

    def fake_select(mensagem, choices, *args, **kwargs):
        capturado["titulos"] = [str(c.title) for c in choices]
        return Pergunta()

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.setenv(start_app.DATABASE_ENV, "")
    monkeypatch.delenv(start_app.DATABASE_ENV, raising=False)
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [
            ("Tarefas", "db-ok", True, []),
            ("Budget", "db-x", False, ["Tarefa (espera title, tem ausente)"]),
        ],
    )
    monkeypatch.setattr(questionary, "select", fake_select)
    console = Console(file=io.StringIO(), force_terminal=False)

    assert start_app._selecionar_database_tarefas(console) is True
    assert any("✓" in t and "Tarefas" in t for t in capturado["titulos"])
    assert any("⚠" in t and "Budget" in t for t in capturado["titulos"])


def test_selecionar_database_incompativel_pede_confirmacao(monkeypatch, tmp_path):
    # Escolher um database sem o schema avisa as colunas que faltam e só grava
    # se a pessoa confirmar.
    import questionary

    class Selecao:
        def ask(self):
            return "db-incompat"

    class Confirma:
        def __init__(self, resposta):
            self.resposta = resposta

        def ask(self):
            return self.resposta

    env_file = tmp_path / ".env"
    env_file.write_text("NOTION_TOKEN=ntn_teste\n", encoding="utf-8")
    monkeypatch.setattr(start_app, "ENV_FILE", env_file)
    monkeypatch.setenv(start_app.DATABASE_ENV, "")
    monkeypatch.delenv(start_app.DATABASE_ENV, raising=False)
    monkeypatch.delenv(start_app.TOKEN_ENV, raising=False)
    monkeypatch.setattr(
        start_app,
        "_buscar_databases",
        lambda token: [("Budget", "db-incompat", False, ["Etapa (espera status, tem ausente)"])],
    )
    monkeypatch.setattr(questionary, "select", lambda *a, **k: Selecao())

    # 1) confirma=False → não grava
    monkeypatch.setattr(questionary, "confirm", lambda *a, **k: Confirma(False))
    saida = io.StringIO()
    console = Console(file=saida, force_terminal=False)
    assert start_app._selecionar_database_tarefas(console) is False
    assert "Etapa (espera status" in saida.getvalue()
    assert "NOTION_DATABASE_ID=db-incompat" not in env_file.read_text()

    # 2) confirma=True → grava mesmo incompatível
    monkeypatch.setattr(questionary, "confirm", lambda *a, **k: Confirma(True))
    console = Console(file=io.StringIO(), force_terminal=False)
    assert start_app._selecionar_database_tarefas(console) is True
    assert "NOTION_DATABASE_ID=db-incompat" in env_file.read_text()


def test_app_web_ativo_valida_health_do_projeto(monkeypatch):
    class Resposta:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'{"status": "ok", "service": "automacoes-notion"}'

    monkeypatch.setattr(start_app.urllib.request, "urlopen", lambda *args, **kwargs: Resposta())

    assert start_app._app_web_ativo() is True


def test_front_web_ativo_valida_html_do_vite(monkeypatch):
    class Resposta:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b'<div id="root"></div><script type="module" src="/src/main.jsx"></script>'

    monkeypatch.setattr(start_app.urllib.request, "urlopen", lambda *args, **kwargs: Resposta())

    assert start_app._front_web_ativo() is True


def test_node_compativel_reflete_requisito_do_vite():
    assert start_app._node_compativel((20, 18, 1)) is False
    assert start_app._node_compativel((20, 19, 0)) is True
    assert start_app._node_compativel((22, 11, 0)) is False
    assert start_app._node_compativel((22, 12, 0)) is True
    assert start_app._node_compativel((25, 9, 0)) is True


def test_comando_front_usa_host_e_porta_padrao():
    runtime = start_app.FrontRuntime(
        node=start_app.Path("/usr/bin/node"),
        npm=start_app.Path("/usr/bin/npm"),
        versao="v22.12.0",
    )

    comando = start_app._comando_front(runtime)

    assert comando == [
        "/usr/bin/npm",
        "run",
        "dev",
        "--",
        "--host",
        start_app.FRONT_HOST,
        "--port",
        start_app.FRONT_PORT,
    ]


def test_abre_navegador_assim_que_health_responde(monkeypatch):
    estados = iter((False, True))
    aberturas = []
    monkeypatch.setattr(start_app, "_app_web_ativo", lambda: next(estados))
    monkeypatch.setattr(start_app, "_front_web_ativo", lambda: True)
    monkeypatch.setattr(start_app.time, "sleep", lambda intervalo: None)
    monkeypatch.setattr(
        start_app.webbrowser,
        "open",
        lambda url: aberturas.append(url) or True,
    )
    console = Console(file=io.StringIO(), force_terminal=False)

    start_app._abrir_navegador_quando_pronto(console, tentativas=2, intervalo=0)

    assert aberturas == [start_app.APP_URL]


def test_iniciar_tudo_usa_defaults_e_sobe_front_api(monkeypatch):
    chamadas = []
    agendamentos = []
    aguardados = []
    runtime = start_app.FrontRuntime(
        node=start_app.Path("/usr/bin/node"),
        npm=start_app.Path("/usr/bin/npm"),
        versao="v22.12.0",
    )

    class Processo:
        def poll(self):
            return None

    monkeypatch.setattr(start_app, "_django_disponivel", lambda: True)
    monkeypatch.setattr(start_app, "_token_configurado", lambda: (True, ".env local"))
    monkeypatch.setattr(start_app, "_garantir_database_tarefas", lambda console: True)
    monkeypatch.setattr(start_app, "_app_web_ativo", lambda: False)
    monkeypatch.setattr(start_app, "_front_web_ativo", lambda: False)
    monkeypatch.setattr(start_app, "_garantir_front_pronto", lambda console: runtime)
    monkeypatch.setattr(start_app, "_ambiente_servidor", lambda: {"DJANGO_DEBUG": "1"})
    monkeypatch.setattr(start_app, "_aplicar_migracoes", lambda console, ambiente: True)
    monkeypatch.setattr(
        start_app,
        "_agendar_abertura_navegador",
        lambda console: agendamentos.append(True),
    )
    monkeypatch.setattr(
        start_app,
        "_aguardar_processos",
        lambda console, processos: aguardados.extend(processos),
    )
    monkeypatch.setattr(
        start_app.subprocess,
        "Popen",
        lambda comando, **kwargs: chamadas.append((comando, kwargs)) or Processo(),
    )
    console = Console(file=io.StringIO(), force_terminal=False)

    start_app.acao_iniciar_tudo(console)

    assert agendamentos == [True]
    assert len(chamadas) == 2
    comando_api, kwargs_api = chamadas[0]
    comando_front, kwargs_front = chamadas[1]
    assert comando_api[-2:] == ["runserver", start_app.API_ENDERECO_PADRAO]
    assert kwargs_api["cwd"] == start_app.SERVIDOR
    assert kwargs_api["env"] == {"DJANGO_DEBUG": "1"}
    assert comando_front == start_app._comando_front(runtime)
    assert kwargs_front["cwd"] == start_app.FRONT
    assert len(aguardados) == 2


def test_iniciar_tudo_reabre_app_que_ja_esta_rodando(monkeypatch):
    aberturas = []
    monkeypatch.setattr(start_app, "_django_disponivel", lambda: True)
    monkeypatch.setattr(start_app, "_token_configurado", lambda: (True, ".env local"))
    monkeypatch.setattr(start_app, "_garantir_database_tarefas", lambda console: True)
    monkeypatch.setattr(start_app, "_app_web_ativo", lambda: True)
    monkeypatch.setattr(start_app, "_front_web_ativo", lambda: True)
    monkeypatch.setattr(
        start_app,
        "_garantir_front_pronto",
        lambda console: start_app.FrontRuntime(
            node=start_app.Path("/usr/bin/node"),
            npm=start_app.Path("/usr/bin/npm"),
            versao="v22.12.0",
        ),
    )
    monkeypatch.setattr(
        start_app.webbrowser,
        "open",
        lambda url: aberturas.append(url) or True,
    )
    monkeypatch.setattr(
        start_app.subprocess,
        "Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("não deve iniciar outro processo")
        ),
    )
    console = Console(file=io.StringIO(), force_terminal=False)

    start_app.acao_iniciar_tudo(console)

    assert aberturas == [start_app.APP_URL]


def test_main_rejeita_acao_desconhecida():
    try:
        start_app.main(["--action", "inexistente"])
    except SystemExit as exc:
        assert "Ação desconhecida" in str(exc)
    else:
        raise AssertionError("main deveria rejeitar uma ação inexistente")
