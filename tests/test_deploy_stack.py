import re
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
    "session_secret",
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
    assert postgres["environment"]["POSTGRES_PASSWORD_FILE"] == (
        "/run/secrets/postgres_password"
    )


def test_cada_secret_referenciado_esta_declarado_no_stack() -> None:
    """SPECSFY: SPEC-0022 US-002 FR-003 NFR-001 AC-005"""
    stack = _stack()
    declarados = stack.get("secrets", {})
    referenciados = {
        nome
        for servico in stack["services"].values()
        for nome in servico.get("secrets", [])
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
