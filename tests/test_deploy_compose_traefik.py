"""Roteamento do Traefik compartilhado no deploy em Compose (SPEC-0045).

Fase RED: `deploy/compose/compose.homolog.yml` ainda não existe.
"""

from __future__ import annotations

import re

from tests._compose_deploy import HOMOLOG, yaml_de

REDE = "n8n-dev-stack_traefik_net"


def _labels(servico: dict) -> list[str]:
    labels = servico.get("labels", [])
    if isinstance(labels, dict):
        return [f"{k}={v}" for k, v in labels.items()]
    return list(labels)


def test_so_o_frontend_e_roteado_por_https() -> None:
    """SPECSFY: SPEC-0045 US-001 FR-001 FR-002 NFR-003 AC-002"""
    servicos = yaml_de(HOMOLOG)["services"]
    labels = "\n".join(_labels(servicos["frontend_ragpipeline"]))
    assert "traefik.enable=true" in labels
    assert "tls.certresolver=mytlschallenge" in labels
    assert "entrypoints=websecure" in labels
    assert "loadbalancer.server.port=3000" in labels
    assert f"traefik.docker.network={REDE}" in labels
    for nome in ("backend_ragpipeline", "worker_ragpipeline", "postgres_ragpipeline"):
        assert "traefik.enable=true" not in _labels(servicos.get(nome, {})), nome
        assert "ports" not in servicos.get(nome, {})


def test_login_tem_limite_hsts_e_redirecionamento() -> None:
    """SPECSFY: SPEC-0045 US-001 FR-002 NFR-001 AC-004"""
    labels = "\n".join(_labels(yaml_de(HOMOLOG)["services"]["frontend_ragpipeline"]))
    assert "redirectscheme.scheme=https" in labels and "redirectscheme.permanent=true" in labels
    assert "headers.stsseconds" in labels
    assert "ratelimit.average" in labels and "ratelimit.burst" in labels
    assert "Path(`/api/v1/auth/login`)" in labels
    prioridades = [int(p) for p in re.findall(r"\.priority=(\d+)", labels)]
    assert max(prioridades) > min(prioridades)


def test_rede_externa_e_nomes_com_prefixo_do_projeto() -> None:
    """SPECSFY: SPEC-0045 US-003 FR-002 NFR-003 AC-012"""
    arquivo = yaml_de(HOMOLOG)
    assert arquivo["networks"]["traefik"] == {"external": True, "name": REDE}
    labels = _labels(arquivo["services"]["frontend_ragpipeline"])
    nomes = {
        m
        for rotulo in labels
        for m in re.findall(r"traefik\.http\.(?:routers|services|middlewares)\.([^.=]+)", rotulo)
    }
    assert nomes and all(n.startswith("ragpipeline-") for n in nomes), nomes
