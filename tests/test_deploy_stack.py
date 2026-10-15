import copy
import re
import socket
from pathlib import Path

import yaml

STACK_PATH = Path(__file__).resolve().parent.parent / "deploy" / "stack.prod.yml"

SERVICOS_ESPERADOS = {
    "backend_ragpipeline",
    "frontend_ragpipeline",
    "worker_ragpipeline",
    "postgres_ragpipeline",
    "qdrant_ragpipeline",
}

SERVICOS_COM_CREDENCIAL = {"backend_ragpipeline", "worker_ragpipeline"}
SECRETS_DE_PRODUCAO = {
    "openrouter_api_key",
    "r2_credentials",
    "conexoes_chave",
    "postgres_password",
}
SERVICOS_DE_APLICACAO = {
    "backend_ragpipeline",
    "frontend_ragpipeline",
    "worker_ragpipeline",
}
SERVICOS_DE_DADOS = {"postgres_ragpipeline", "qdrant_ragpipeline"}
SERVICOS_COM_PLACEMENT = SERVICOS_DE_APLICACAO | SERVICOS_DE_DADOS
CONSTRAINT_VALIDA = re.compile(r"^\s*node\.[\w.]+\s*==\s*\S+\s*$")


def _stack() -> dict:
    return yaml.safe_load(STACK_PATH.read_text())


def test_stack_declara_os_cinco_servicos_esperados() -> None:
    """SPECSFY: SPEC-0022 US-001 FR-001 FR-002 AC-001"""
    stack = _stack()
    assert SERVICOS_ESPERADOS.issubset(stack["services"].keys())


def test_servicos_python_executam_venv_sem_cache_uv_em_runtime() -> None:
    """SPECSFY: SPEC-0022 US-001 FR-001 FR-002 NFR-001 AC-001"""
    stack = _stack()
    for nome in ("backend_ragpipeline", "worker_ragpipeline"):
        comando = "\n".join(str(item) for item in stack["services"][nome]["command"])
        assert "uv run" not in comando
        assert "exec .venv/bin/python" in comando


def test_volumes_de_producao_sao_externos_e_distintos_dos_de_teste() -> None:
    """SPECSFY: SPEC-0022 US-001 FR-001 FR-002 AC-002"""
    stack = _stack()
    volumes = stack["volumes"]
    for nome in ("postgres_data_ragpipeline", "qdrant_data_ragpipeline"):
        assert volumes[nome]["external"] is True
        assert nome != "rag-pipeline-test-postgres"


def test_credenciais_sensiveis_sao_referencias_a_secrets() -> None:
    """SPECSFY: SPEC-0022 US-002 FR-003 AC-004"""
    stack = _stack()
    for nome in SERVICOS_COM_CREDENCIAL:
        servico = stack["services"][nome]
        secrets_do_servico = set(servico.get("secrets", []))
        assert SECRETS_DE_PRODUCAO.issubset(secrets_do_servico)
        comando = "\n".join(str(item) for item in servico.get("command", []))
        for secret in SECRETS_DE_PRODUCAO:
            assert f"/run/secrets/{secret}" in comando
        for valor in (servico.get("environment") or {}).values():
            assert str(valor) not in SECRETS_DE_PRODUCAO

    postgres = stack["services"]["postgres_ragpipeline"]
    assert "postgres_password" in postgres.get("secrets", [])
    assert postgres["environment"]["POSTGRES_PASSWORD_FILE"] == ("/run/secrets/postgres_password")


def test_cada_secret_referenciado_esta_declarado_no_stack() -> None:
    """SPECSFY: SPEC-0022 US-002 FR-003 NFR-001 AC-005"""
    stack = _stack()
    declarados = stack.get("secrets", {})
    referenciados = {
        nome for servico in stack["services"].values() for nome in servico.get("secrets", [])
    }
    for nome in referenciados:
        assert nome in declarados
        assert declarados[nome]["external"] is True


def test_nenhum_valor_de_secret_aparece_em_texto_puro() -> None:
    """SPECSFY: SPEC-0022 US-002 FR-003 AC-006"""
    stack = _stack()
    for definicao in stack.get("secrets", {}).values():
        assert definicao.get("external") is True
        assert "file" not in definicao


def test_servicos_tem_placement_compativel_com_imagens_locais() -> None:
    """SPECSFY: SPEC-0022 US-003 FR-004 AC-007"""
    stack = _stack()
    for nome in SERVICOS_DE_APLICACAO:
        constraints = stack["services"][nome]["deploy"]["placement"]["constraints"]
        assert "node.hostname == ${APPLICATION_NODE_HOSTNAME}" in constraints
    for nome in SERVICOS_DE_DADOS:
        constraints = stack["services"][nome]["deploy"]["placement"]["constraints"]
        assert "node.hostname == ${DATABASE_NODE_HOSTNAME}" in constraints


def test_stack_conecta_rede_externa_network_swarm_public() -> None:
    """SPECSFY: SPEC-0022 US-003 FR-004 AC-008"""
    stack = _stack()
    assert stack["networks"]["network_swarm_public"]["external"] is True
    for nome in SERVICOS_ESPERADOS:
        assert "network_swarm_public" in stack["services"][nome]["networks"]
    nomes_servico = stack["services"]
    assert not any("traefik" in nome.lower() or "proxy" in nome.lower() for nome in nomes_servico)


def test_constraints_de_placement_sao_bem_formadas_e_escopadas_por_servico() -> None:
    """SPECSFY: SPEC-0022 US-003 FR-004 NFR-001 AC-009"""
    stack = _stack()
    assert "placement" not in stack
    assert "constraints" not in stack
    for nome in SERVICOS_COM_PLACEMENT:
        constraints = stack["services"][nome]["deploy"]["placement"]["constraints"]
        assert constraints
        assert all(CONSTRAINT_VALIDA.match(item) for item in constraints)


def test_chave_de_cifra_das_conexoes_chega_ao_backend_e_ao_worker_so_por_secret() -> None:
    """SPECSFY: SPEC-0026 FR-002 NFR-001 NFR-005 AC-013"""
    stack = _stack()
    assert stack["secrets"]["conexoes_chave"]["external"] is True
    for nome in SERVICOS_COM_CREDENCIAL:
        servico = stack["services"][nome]
        comando = "\n".join(str(item) for item in servico["command"])
        assert "conexoes_chave" in servico["secrets"]
        assert "APP_CONEXOES_CHAVE_FILE=/run/secrets/conexoes_chave" in comando
        ambiente = servico.get("environment") or {}
        assert "APP_CONEXOES_CHAVE" not in ambiente
        assert "APP_CONEXOES_CHAVE_FILE" not in ambiente


# --- SPEC-0027: secrets versionados por variável e sem session_secret ----------

LOCAL_PATH = STACK_PATH.with_name("stack.local.yml")
NOME_POR_VARIAVEL = re.compile(
    r"^\$\{(OPENROUTER_API_KEY|R2_CREDENTIALS|POSTGRES_PASSWORD|CONEXOES_CHAVE)_SECRET:-"
    r"(openrouter_api_key|r2_credentials|postgres_password|conexoes_chave)_v1\}$"
)


def test_stack_usa_secrets_externos_versionados_e_nao_tem_session_secret() -> None:
    """SPECSFY: SPEC-0027 US-002 FR-007 AC-009"""
    texto = STACK_PATH.read_text()
    stack = yaml.safe_load(texto)

    assert "session_secret" not in texto
    assert "APP_SESSION_SECRET" not in texto
    assert set(stack["secrets"]) == {
        "openrouter_api_key",
        "r2_credentials",
        "postgres_password",
        "conexoes_chave",
    }
    for logico, definicao in stack["secrets"].items():
        assert definicao["external"] is True
        assert NOME_POR_VARIAVEL.match(definicao["name"]), (logico, definicao)
    assert "postgres_password" in stack["services"]["postgres_ragpipeline"]["secrets"]
    for nome in SERVICOS_COM_CREDENCIAL:
        assert "conexoes_chave" in stack["services"][nome]["secrets"]


def test_override_local_nao_mapeia_secrets_por_nome_fixo() -> None:
    """SPECSFY: SPEC-0027 US-004 FR-007 FR-008 AC-015"""
    local = yaml.safe_load(LOCAL_PATH.read_text())

    assert "secrets" not in local
    assert "openrouter_api_key_local" not in LOCAL_PATH.read_text()
    for nome in SERVICOS_COM_CREDENCIAL:
        assert "secrets" not in local["services"][nome]
        assert local["services"][nome]["volumes"]
    assert "uploads_local_ragpipeline" in local["volumes"]


# --- SPEC-0032: domínio, HTTPS e reverse proxy (leitura do arquivo, sem rede) ---------

DOMINIO_DE_TESTE = "app-teste.invalid"
FRONTEND = "frontend_ragpipeline"
LOGIN_PATH = "/api/v1/auth/login"
_VARIAVEL = re.compile(r"\$\{(\w+)(?::-([^}]*))?\}")
_HOST_LITERAL = re.compile(r"Host(?:Regexp)?\(`([^`$]+)`\)")


def _interpolar(texto: str, env: dict[str, str] | None = None) -> str:
    """Resolve `${VAR}` e `${VAR:-padrão}` como o `docker stack deploy` faz."""
    env = env or {}

    def trocar(m: re.Match) -> str:
        return env.get(m.group(1)) or (m.group(2) if m.group(2) is not None else "")

    return _VARIAVEL.sub(trocar, texto)


def _labels(stack: dict, servico: str, env: dict[str, str] | None = None) -> dict[str, str]:
    """Labels do serviço (`deploy.labels` e `labels`), com chaves em minúsculas."""
    definicao = stack["services"][servico]
    brutas: list[str] = []
    for origem in ((definicao.get("deploy") or {}).get("labels"), definicao.get("labels")):
        if isinstance(origem, dict):
            brutas.extend(f"{k}={v}" for k, v in origem.items())
        else:
            brutas.extend(origem or [])
    labels: dict[str, str] = {}
    for item in brutas:
        chave, _, valor = str(item).partition("=")
        labels[chave.strip().lower()] = _interpolar(valor.strip(), env)
    return labels


def _roteadores(labels: dict[str, str]) -> dict[str, dict[str, str]]:
    roteadores: dict[str, dict[str, str]] = {}
    for chave, valor in labels.items():
        m = re.fullmatch(r"traefik\.http\.routers\.([^.]+)\.(.+)", chave)
        if m:
            roteadores.setdefault(m.group(1), {})[m.group(2)] = valor
    return roteadores


def _middlewares(labels: dict[str, str]) -> dict[str, dict[str, str]]:
    middlewares: dict[str, dict[str, str]] = {}
    for chave, valor in labels.items():
        m = re.fullmatch(r"traefik\.http\.middlewares\.([^.]+)\.(.+)", chave)
        if m:
            middlewares.setdefault(m.group(1), {})[m.group(2)] = valor
    return middlewares


def _nomes_de_middlewares(roteador: dict[str, str]) -> list[str]:
    bruto = roteador.get("middlewares", "")
    return [n.strip().split("@")[0] for n in bruto.split(",") if n.strip()]


def _roteador_https(labels: dict[str, str]) -> tuple[str, dict[str, str]]:
    """O roteador geral do domínio: o que tem certificado e não é o do login."""
    candidatos = [
        (nome, r)
        for nome, r in _roteadores(labels).items()
        if "tls.certresolver" in r and LOGIN_PATH not in r.get("rule", "")
    ]
    assert len(candidatos) == 1, f"esperava um roteador HTTPS geral, achei {len(candidatos)}"
    return candidatos[0]


def _roteador_http(labels: dict[str, str], entrypoint: str = "web") -> dict[str, str]:
    candidatos = [r for r in _roteadores(labels).values() if r.get("entrypoints") == entrypoint]
    assert len(candidatos) == 1, f"esperava um roteador no ponto de entrada {entrypoint}"
    return candidatos[0]


def _roteador_do_login(labels: dict[str, str]) -> tuple[str, dict[str, str]]:
    candidatos = [
        (nome, r) for nome, r in _roteadores(labels).items() if LOGIN_PATH in r.get("rule", "")
    ]
    assert len(candidatos) == 1, "esperava um roteador próprio para o login"
    return candidatos[0]


def _middleware_de_cabecalhos(labels: dict[str, str]) -> tuple[str, dict[str, str]]:
    candidatos = [
        (nome, m) for nome, m in _middlewares(labels).items() if "headers.stsseconds" in m
    ]
    assert len(candidatos) == 1, "esperava um middleware de cabeçalhos com HSTS"
    return candidatos[0]


def _middleware_de_limite(labels: dict[str, str]) -> tuple[str, dict[str, str]]:
    candidatos = [
        (nome, m)
        for nome, m in _middlewares(labels).items()
        if any(chave.startswith("ratelimit.") for chave in m)
    ]
    assert len(candidatos) == 1, "esperava um middleware de limite de tentativas"
    return candidatos[0]


def _servicos_expostos(stack: dict) -> set[str]:
    return {
        nome for nome in stack["services"] if _labels(stack, nome).get("traefik.enable") == "true"
    }


def _dominios_literais(texto: str) -> list[str]:
    return _HOST_LITERAL.findall(texto)


def _adicionar_label(stack: dict, servico: str, label: str) -> None:
    deploy = stack["services"][servico].setdefault("deploy", {})
    existentes = deploy.setdefault("labels", [])
    if isinstance(existentes, dict):
        chave, _, valor = label.partition("=")
        existentes[chave] = valor
    else:
        existentes.append(label)


def test_frontend_e_exposto_por_dominio_de_variavel_e_so_ele() -> None:
    """SPECSFY: SPEC-0032 US-001 FR-001 NFR-001 NFR-002 AC-001"""
    stack = _stack()
    labels = _labels(stack, FRONTEND, {"DOMINIO_RAGPIPELINE": DOMINIO_DE_TESTE})

    assert labels.get("traefik.enable") == "true"
    _, https = _roteador_https(labels)
    assert f"Host(`{DOMINIO_DE_TESTE}`)" in https["rule"]
    assert "${DOMINIO_RAGPIPELINE}" in STACK_PATH.read_text()
    assert _servicos_expostos(stack) == {FRONTEND}
    assert _dominios_literais(STACK_PATH.read_text()) == []


def test_resolvedor_e_entrypoint_tem_padrao_e_aceitam_variavel() -> None:
    """SPECSFY: SPEC-0032 US-001 FR-003 NFR-001 AC-002"""
    stack = _stack()

    _, padrao = _roteador_https(_labels(stack, FRONTEND))
    assert padrao["tls.certresolver"] == "letsencryptresolver"
    assert padrao["entrypoints"] == "websecure"

    _, definido = _roteador_https(
        _labels(
            stack,
            FRONTEND,
            {"TRAEFIK_CERT_RESOLVER": "outro-resolvedor", "TRAEFIK_ENTRYPOINT_HTTPS": "https-alt"},
        )
    )
    assert definido["tls.certresolver"] == "outro-resolvedor"
    assert definido["entrypoints"] == "https-alt"


def test_roteador_http_redireciona_permanentemente_para_https() -> None:
    """SPECSFY: SPEC-0032 US-002 FR-002 FR-003 AC-004"""
    labels = _labels(_stack(), FRONTEND, {"DOMINIO_RAGPIPELINE": DOMINIO_DE_TESTE})

    http = _roteador_http(labels)
    assert f"Host(`{DOMINIO_DE_TESTE}`)" in http["rule"]
    nomes = _nomes_de_middlewares(http)
    redirecionamentos = [
        _middlewares(labels)[n]
        for n in nomes
        if "redirectscheme.scheme" in _middlewares(labels).get(n, {})
    ]
    assert len(redirecionamentos) == 1
    assert redirecionamentos[0]["redirectscheme.scheme"] == "https"
    assert redirecionamentos[0]["redirectscheme.permanent"] == "true"

    outro = _roteador_http(
        _labels(_stack(), FRONTEND, {"TRAEFIK_ENTRYPOINT_HTTP": "http-alt"}), "http-alt"
    )
    assert outro["entrypoints"] == "http-alt"


def test_hsts_tem_validade_curta_e_aceita_variavel() -> None:
    """SPECSFY: SPEC-0032 US-002 FR-002 FR-003 AC-005"""
    stack = _stack()

    nome, padrao = _middleware_de_cabecalhos(_labels(stack, FRONTEND))
    assert padrao["headers.stsseconds"] == "86400"
    _, https = _roteador_https(_labels(stack, FRONTEND))
    assert nome in _nomes_de_middlewares(https)

    _, definido = _middleware_de_cabecalhos(
        _labels(stack, FRONTEND, {"HSTS_MAX_AGE_SEGUNDOS": "3600"})
    )
    assert definido["headers.stsseconds"] == "3600"


def test_hsts_sem_includesubdomains_nem_preload() -> None:
    """SPECSFY: SPEC-0032 US-002 FR-002 AC-006"""
    _, cabecalhos = _middleware_de_cabecalhos(_labels(_stack(), FRONTEND))

    assert cabecalhos.get("headers.stsincludesubdomains", "false") == "false"
    assert cabecalhos.get("headers.stspreload", "false") == "false"


def test_login_tem_roteador_proprio_com_prioridade_e_limite() -> None:
    """SPECSFY: SPEC-0032 US-003 FR-004 NFR-002 AC-007"""
    labels = _labels(_stack(), FRONTEND)

    _, login = _roteador_do_login(labels)
    assert "Method(`POST`)" in login["rule"]
    assert "tls.certresolver" in login
    nome_limite, _ = _middleware_de_limite(labels)
    assert nome_limite in _nomes_de_middlewares(login)

    _, geral = _roteador_https(labels)
    assert nome_limite not in _nomes_de_middlewares(geral)
    prioridade_geral = int(geral["priority"]) if "priority" in geral else len(geral["rule"])
    assert int(login["priority"]) > prioridade_geral


def test_limite_do_login_por_endereco_com_media_e_rajada_configuraveis() -> None:
    """SPECSFY: SPEC-0032 US-003 FR-004 AC-008"""
    stack = _stack()

    _, padrao = _middleware_de_limite(_labels(stack, FRONTEND))
    assert not any("requestheadername" in c or "requesthost" in c for c in padrao)
    assert padrao["ratelimit.period"] == "1m"
    assert padrao["ratelimit.average"] == "10"
    assert padrao["ratelimit.burst"] == "20"

    _, definido = _middleware_de_limite(
        _labels(stack, FRONTEND, {"LOGIN_RATE_LIMIT_MEDIA": "30", "LOGIN_RATE_LIMIT_RAJADA": "60"})
    )
    assert definido["ratelimit.average"] == "30"
    assert definido["ratelimit.burst"] == "60"


def test_limite_do_login_declara_rajada_que_recusa_o_excesso() -> None:
    """SPECSFY: SPEC-0032 US-003 FR-004 AC-009"""
    _, limite = _middleware_de_limite(_labels(_stack(), FRONTEND))

    assert int(limite["ratelimit.burst"]) > 0
    assert int(limite["ratelimit.average"]) > 0
    assert int(limite["ratelimit.burst"]) >= int(limite["ratelimit.average"])


def test_testes_de_dominio_leem_o_stack_sem_rede(monkeypatch) -> None:
    """SPECSFY: SPEC-0032 US-004 FR-006 NFR-001 AC-013"""

    def sem_rede(*args, **kwargs):
        raise AssertionError("os testes de domínio não podem abrir conexão de rede")

    monkeypatch.setattr(socket, "socket", sem_rede)
    monkeypatch.setattr(socket, "create_connection", sem_rede)
    monkeypatch.setattr(socket, "getaddrinfo", sem_rede)
    for variavel in ("APP_DATABASE_URL", "DATABASE_URL"):
        monkeypatch.delenv(variavel, raising=False)

    labels = _labels(_stack(), FRONTEND, {"DOMINIO_RAGPIPELINE": DOMINIO_DE_TESTE})

    assert labels, "o frontend deveria declarar labels lidas só do arquivo"
    assert _roteadores(labels)


def test_stack_com_backend_exposto_e_detectado() -> None:
    """SPECSFY: SPEC-0032 US-004 FR-006 NFR-002 FR-001 AC-014"""
    stack = _stack()
    assert _servicos_expostos(stack) == {FRONTEND}

    alterado = copy.deepcopy(stack)
    _adicionar_label(alterado, "backend_ragpipeline", "traefik.enable=true")

    assert _servicos_expostos(alterado) == {FRONTEND, "backend_ragpipeline"}
    assert _servicos_expostos(alterado) != _servicos_expostos(stack)


def test_dominio_literal_na_regra_e_detectado() -> None:
    """SPECSFY: SPEC-0032 US-004 FR-006 NFR-001 FR-001 AC-015"""
    assert _dominios_literais("rule: Host(`exemplo.com`)") == ["exemplo.com"]
    assert _dominios_literais("rule: Host(`${DOMINIO_RAGPIPELINE}`)") == []

    # Preservar a referência: sem ambiente, o helper interpola a variável para
    # vazio antes de esta guarda poder conferir se a regra é parametrizada.
    labels = _labels(_stack(), FRONTEND, {"DOMINIO_RAGPIPELINE": "${DOMINIO_RAGPIPELINE}"})
    regras = [r["rule"] for r in _roteadores(labels).values()]
    assert regras, "o frontend deveria declarar regras de roteamento"
    assert all("${DOMINIO_RAGPIPELINE}" in r for r in regras)
    assert _dominios_literais(STACK_PATH.read_text()) == []


# SPEC-0034 — backup automático do Postgres de produção -----------------------

LOCAL_PATH = Path(__file__).resolve().parent.parent / "deploy" / "stack.local.yml"
SECRETS_DE_BACKUP = {"backup_chave", "backup_r2_credentials", "backup_avisos"}


def test_stack_declara_o_servico_de_backup_preso_ao_no_de_dados() -> None:
    """SPECSFY: SPEC-0034 US-004 FR-008 NFR-003 AC-015"""
    stack = _stack()
    servicos = stack["services"]

    assert "backup_ragpipeline" in servicos
    backup = servicos["backup_ragpipeline"]
    assert not backup.get("ports"), "o serviço de backup não publica portas"
    assert not backup.get("volumes"), "o dump não é guardado em volume"
    restricoes = backup["deploy"]["placement"]["constraints"]
    assert any("DATABASE_NODE_HOSTNAME" in restricao for restricao in restricoes)
    assert set(backup["secrets"]) == SECRETS_DE_BACKUP | {"postgres_password"}
    ambiente = backup.get("environment", {})
    chaves = ambiente if isinstance(ambiente, dict) else {item.split("=")[0] for item in ambiente}
    assert "BACKUP_TIMEOUT_SEGUNDOS" in chaves
    for nome in SECRETS_DE_BACKUP:
        definicao = stack["secrets"][nome]
        assert definicao["external"] is True
        assert definicao["name"].startswith("${") and f"{nome}_v1" in definicao["name"]


def test_override_local_ensaia_o_backup_com_armazenamento_s3_local() -> None:
    """SPECSFY: SPEC-0034 US-004 FR-001 FR-008 AC-016"""
    local = yaml.safe_load(LOCAL_PATH.read_text())
    servicos = local["services"]

    armazenamentos = [
        nome for nome, servico in servicos.items() if "minio" in str(servico.get("image", ""))
    ]
    assert armazenamentos, "o override local precisa de um armazenamento compatível com S3"
    texto = LOCAL_PATH.read_text()
    assert "r2.cloudflarestorage.com" not in texto
    assert "AWS_SECRET_ACCESS_KEY" not in texto, "nenhuma credencial no override"
