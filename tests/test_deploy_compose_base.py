"""Conjunto base do deploy em Compose (SPEC-0045).

Fase RED: `deploy/compose/compose.yml` ainda não existe. Os casos leem o arquivo sem rede.
"""

from __future__ import annotations

from tests._compose_deploy import COMPOSE, SERVICOS, yaml_de

APLICACAO = ("backend_ragpipeline", "worker_ragpipeline", "frontend_ragpipeline")


def test_conjunto_tem_cinco_servicos_enxutos_e_seguros() -> None:
    """SPECSFY: SPEC-0045 US-001 FR-001 FR-006 NFR-001 AC-001"""
    servicos = yaml_de(COMPOSE)["services"]
    assert set(servicos) == set(SERVICOS)
    for nome, servico in servicos.items():
        assert "ports" not in servico, f"{nome} publica porta no host"
        assert servico.get("restart") == "unless-stopped", nome
        assert servico.get("mem_limit") and servico.get("cpus"), f"{nome} sem limite"
        assert servico.get("healthcheck"), f"{nome} sem healthcheck"
        assert "deploy" not in servico, f"{nome} usa deploy: do Swarm"
    for nome in APLICACAO:
        servico = servicos[nome]
        assert servico.get("read_only") is True, nome
        assert servico.get("cap_drop") == ["ALL"], nome
        assert "no-new-privileges:true" in servico.get("security_opt", []), nome
        assert servico.get("init") is True, nome
    assert "ragpipeline_postgres_data" in yaml_de(COMPOSE)["volumes"]


def test_aplicacao_espera_o_postgres_ficar_saudavel() -> None:
    """SPECSFY: SPEC-0045 US-001 FR-001 FR-006 NFR-003 AC-003"""
    servicos = yaml_de(COMPOSE)["services"]
    teste = " ".join(servicos["postgres_ragpipeline"]["healthcheck"]["test"])
    assert "pg_isready" in teste
    for nome in ("backend_ragpipeline", "worker_ragpipeline"):
        depende = servicos[nome]["depends_on"]["postgres_ragpipeline"]
        assert depende["condition"] == "service_healthy", nome


def test_backup_alcanca_o_postgres_em_container_sem_tls() -> None:
    """SPECSFY: SPEC-0045 US-001 FR-006 NFR-001 AC-020"""
    backup = yaml_de(COMPOSE)["services"]["backup_ragpipeline"]
    ambiente = backup["environment"]
    assert ambiente["PGHOST"] == "postgres_ragpipeline"
    assert ambiente["PGSSLMODE"] == "disable"
    segredos = set(backup["secrets"])
    assert {
        "backup_chave",
        "backup_r2_credentials",
        "backup_avisos",
        "postgres_password",
    } <= segredos
    assert "placement" not in backup.get("deploy", {})
