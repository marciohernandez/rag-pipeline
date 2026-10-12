"""Provisionamento e conferência dos secrets do Swarm (SPEC-0027).

Fase RED: `deploy/secrets.sh` ainda não existe. Os casos exercitam o script real
com um `docker` falso no `PATH` que simula o armazenamento de secrets do Swarm.
"""

from __future__ import annotations

import re
from pathlib import Path

from cryptography.fernet import Fernet

from tests._docker_falso import (
    RAIZ,
    Ambiente,
    entrada_criar,
    todos_os_secrets,
    valores_gerados,
)

R2_ASSINATURA = ("APP_R2_BUCKET=bucket-sentinela", "APP_R2_ENDPOINT_URL=https://r2.exemplo.com")


def test_criar_pela_primeira_vez_pede_so_o_que_vem_de_terceiros(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-001 FR-001 FR-002 NFR-001 NFR-003 NFR-004 AC-001"""
    amb = Ambiente(tmp_path)

    resultado = amb.secrets_script("criar", "--entrada-padrao", entrada=entrada_criar())

    assert resultado.returncode == 0, resultado.stderr
    assert amb.nomes() == [
        "conexoes_chave_v1",
        "openrouter_api_key_v1",
        "postgres_password_v1",
        "r2_credentials_v1",
    ]
    assert amb.valor("openrouter_api_key_v1") == "sk-or-sentinela-0027"
    r2 = amb.valor("r2_credentials_v1")
    assert all(trecho in r2 for trecho in R2_ASSINATURA)
    assert "APP_R2_ACCESS_KEY_ID=AKIASENTINELA0027" in r2
    assert "APP_R2_SECRET_ACCESS_KEY=segredo-r2-sentinela-0027" in r2
    for linha in amb.criacoes():
        assert re.fullmatch(r"secret create \S+ -", linha), linha
    assert "openrouter_api_key_v1" in resultado.stdout


def test_valores_gerados_aparecem_uma_unica_vez_e_a_chave_e_fernet_valida(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-001 FR-002 NFR-003 AC-002"""
    amb = Ambiente(tmp_path)

    primeira = amb.secrets_script("criar", "--entrada-padrao", entrada=entrada_criar())
    gerados = valores_gerados(primeira.stdout + primeira.stderr)

    assert set(gerados) == {"postgres_password_v1", "conexoes_chave_v1"}
    senha = gerados["postgres_password_v1"]
    assert re.fullmatch(r"[A-Za-z0-9]{32}", senha)
    chave = gerados["conexoes_chave_v1"]
    assert len(chave) == 44
    assert Fernet(chave.encode())
    assert amb.valor("postgres_password_v1") == senha
    assert (primeira.stdout + primeira.stderr).count(senha) == 1
    segunda = amb.secrets_script("criar", "--entrada-padrao", entrada="")
    assert senha not in segunda.stdout + segunda.stderr
    assert chave not in segunda.stdout + segunda.stderr


def test_criar_com_nome_explicito_recusa_o_secret_que_ja_existe(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-001 FR-001 FR-003 NFR-002 AC-003"""
    amb = Ambiente(tmp_path, {"openrouter_api_key_v1": "valor-antigo"})

    resultado = amb.secrets_script("criar", "openrouter_api_key", "--entrada-padrao", entrada="")

    assert resultado.returncode == 1
    assert "openrouter_api_key" in resultado.stderr + resultado.stdout
    assert "já existe" in resultado.stderr + resultado.stdout
    assert "trocar" in resultado.stderr + resultado.stdout
    assert amb.criacoes() == []
    assert amb.valor("openrouter_api_key_v1") == "valor-antigo"


def test_criar_sem_nomes_completa_somente_os_ausentes(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-001 FR-002 FR-003 NFR-002 AC-004"""
    amb = Ambiente(
        tmp_path,
        {"openrouter_api_key_v1": "chave-antiga", "postgres_password_v1": "senha-antiga"},
    )
    entrada = (
        "bucket-sentinela\nhttps://r2.exemplo.com\nAKIASENTINELA0027\nsegredo-r2-sentinela-0027\n"
    )

    resultado = amb.secrets_script("criar", "--entrada-padrao", entrada=entrada)

    assert resultado.returncode == 0, resultado.stderr
    assert amb.nomes() == [
        "conexoes_chave_v1",
        "openrouter_api_key_v1",
        "postgres_password_v1",
        "r2_credentials_v1",
    ]
    assert amb.valor("openrouter_api_key_v1") == "chave-antiga"
    assert amb.valor("postgres_password_v1") == "senha-antiga"
    assert "preservado" in resultado.stdout + resultado.stderr
    assert len(amb.criacoes()) == 2


def test_entrada_vazia_ou_invalida_e_recusada_sem_criar_nada(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-001 FR-002 FR-003 FR-009 NFR-004 AC-005"""
    amb = Ambiente(tmp_path)

    vazia = amb.secrets_script("criar", "--entrada-padrao", entrada=entrada_criar(chave=""))
    invalida = amb.secrets_script(
        "criar", "--entrada-padrao", entrada=entrada_criar(endpoint="ftp://r2.exemplo.com")
    )

    assert vazia.returncode == 1 and invalida.returncode == 1
    assert "openrouter" in (vazia.stderr + vazia.stdout).lower()
    assert "endpoint" in (invalida.stderr + invalida.stdout).lower()
    assert "ftp://r2.exemplo.com" not in invalida.stderr + invalida.stdout
    assert amb.criacoes() == []
    assert amb.nomes() == []


def test_resolver_devolve_a_versao_mais_alta_de_cada_ambiente(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 US-004 FR-005 FR-008 AC-006"""
    amb = Ambiente(
        tmp_path,
        {
            "openrouter_api_key_v1": "valor-sentinela-v1",
            "openrouter_api_key_v2": "valor-sentinela-v2",
            "openrouter_api_key_local_v1": "valor-sentinela-local",
        },
    )

    producao = amb.secrets_script("resolver")
    local = amb.secrets_script("resolver", "--ambiente", "local")

    assert producao.returncode == 0 and local.returncode == 0
    assert "OPENROUTER_API_KEY_SECRET=openrouter_api_key_v2" in producao.stdout.splitlines()
    assert "_local_" not in producao.stdout
    assert "OPENROUTER_API_KEY_SECRET=openrouter_api_key_local_v1" in local.stdout.splitlines()
    assert "valor-sentinela" not in producao.stdout + local.stdout + producao.stderr + local.stderr


def test_trocar_cria_a_proxima_versao_e_preserva_a_anterior(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-003 FR-004 FR-005 NFR-002 AC-010"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.secrets_script(
        "trocar", "openrouter_api_key", "--entrada-padrao", entrada="nova-chave-sentinela\n"
    )

    assert resultado.returncode == 0, resultado.stderr
    assert "openrouter_api_key_v2" in resultado.stdout
    assert amb.valor("openrouter_api_key_v2") == "nova-chave-sentinela"
    assert amb.valor("openrouter_api_key_v1") == "valor-existente-openrouter_api_key-v1"
    assert "próximo deploy" in resultado.stdout + resultado.stderr
    assert (
        "OPENROUTER_API_KEY_SECRET=openrouter_api_key_v2" in amb.secrets_script("resolver").stdout
    )


def test_troca_de_postgres_e_conexoes_e_bloqueada_por_padrao(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-003 FR-004 FR-010 NFR-004 AC-011"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    postgres = amb.secrets_script("trocar", "postgres_password", "--entrada-padrao", entrada="")
    conexoes = amb.secrets_script("trocar", "conexoes_chave", "--entrada-padrao", entrada="")

    assert postgres.returncode == 1 and conexoes.returncode == 1
    assert "ALTER USER" in postgres.stdout + postgres.stderr
    assert "recadastrar" in conexoes.stdout + conexoes.stderr
    assert "--confirmar-consequencia" in postgres.stdout + postgres.stderr
    assert amb.criacoes() == []
    assert amb.nomes() == sorted(todos_os_secrets())


def test_troca_perigosa_so_prossegue_com_parametro_e_confirmacao_digitada(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-003 FR-004 FR-010 NFR-001 AC-012"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    errada = amb.secrets_script(
        "trocar",
        "postgres_password",
        "--confirmar-consequencia",
        "--entrada-padrao",
        entrada="errado\n",
    )
    assert errada.returncode == 1
    assert "postgres_password_v2" not in amb.nomes()

    certa = amb.secrets_script(
        "trocar",
        "postgres_password",
        "--confirmar-consequencia",
        "--entrada-padrao",
        entrada="postgres_password\n",
    )

    assert certa.returncode == 0, certa.stderr
    assert "ALTER USER" in certa.stdout + certa.stderr
    novo = valores_gerados(certa.stdout + certa.stderr)["postgres_password_v2"]
    assert re.fullmatch(r"[A-Za-z0-9]{32}", novo)
    assert amb.valor("postgres_password_v2") == novo
    assert (certa.stdout + certa.stderr).count(novo) == 1


def test_falha_na_criacao_da_nova_versao_mantem_a_anterior_vigente(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-003 FR-004 NFR-002 AC-013"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    entrada = "bucket-novo\nhttps://r2.exemplo.com\nAKIANOVA\nsegredo-novo\n"

    resultado = amb.secrets_script(
        "trocar",
        "r2_credentials",
        "--entrada-padrao",
        entrada=entrada,
        FAKE_FALHAR_CRIAR="r2_credentials_v2",
    )

    assert resultado.returncode != 0
    assert "v1" in resultado.stdout + resultado.stderr
    assert "r2_credentials_v2" not in amb.nomes()
    assert amb.valor("r2_credentials_v1") == "valor-existente-r2_credentials-v1"
    assert "R2_CREDENTIALS_SECRET=r2_credentials_v1" in amb.secrets_script("resolver").stdout


def test_ensaio_local_cria_secrets_ficticios_sem_perguntar(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-004 FR-008 NFR-003 AC-014"""
    amb = Ambiente(tmp_path)

    resultado = amb.secrets_script("criar", "--ambiente", "local", entrada="")

    assert resultado.returncode == 0, resultado.stderr
    assert amb.nomes() == [
        "conexoes_chave_local_v1",
        "openrouter_api_key_local_v1",
        "postgres_password_local_v1",
        "r2_credentials_local_v1",
    ]
    assert not amb.valor("openrouter_api_key_local_v1").startswith("sk-or-")
    assert not re.search(r"^APP_R2_", amb.valor("r2_credentials_local_v1"), re.MULTILINE)
    assert re.fullmatch(r"[A-Za-z0-9]{32}", amb.valor("postgres_password_local_v1"))
    assert Fernet(amb.valor("conexoes_chave_local_v1").encode())


def test_nenhum_valor_aparece_em_argumento_saida_ou_arquivo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-001 US-003 FR-009 NFR-001 AC-016"""
    amb = Ambiente(tmp_path)
    criar = amb.secrets_script("criar", "--entrada-padrao", entrada=entrada_criar())
    trocar = amb.secrets_script(
        "trocar", "openrouter_api_key", "--entrada-padrao", entrada="nova-chave-sentinela\n"
    )
    sentinelas = [
        "sk-or-sentinela-0027",
        "AKIASENTINELA0027",
        "segredo-r2-sentinela-0027",
        "nova-chave-sentinela",
    ]

    assert criar.returncode == 0 and trocar.returncode == 0
    saidas = criar.stdout + criar.stderr + trocar.stdout + trocar.stderr
    argumentos = "\n".join(amb.chamadas())
    outros_arquivos = "\n".join(
        arquivo.read_text(errors="ignore")
        for arquivo in tmp_path.rglob("*")
        if arquivo.is_file()
        and (amb.estado / "secrets") not in arquivo.parents
        and arquivo.is_symlink() is False
        and arquivo.name not in {"chamadas.log", "docker"}
    )
    for sentinela in sentinelas:
        assert sentinela not in saidas
        assert sentinela not in argumentos
        assert sentinela not in outros_arquivos


def test_falha_clara_sem_docker_ou_fora_do_manager(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 FR-001 FR-009 NFR-004 AC-017"""
    amb = Ambiente(tmp_path)

    sem_docker = amb.secrets_script(
        "criar", "--entrada-padrao", entrada=entrada_criar(), com_docker=False
    )
    sem_manager = amb.secrets_script(
        "criar", "--entrada-padrao", entrada=entrada_criar(), FAKE_MANAGER="false"
    )

    assert sem_docker.returncode == 2
    assert "docker" in (sem_docker.stdout + sem_docker.stderr).lower()
    assert sem_manager.returncode == 2
    assert "manager" in (sem_manager.stdout + sem_manager.stderr).lower()
    assert amb.criacoes() == []
    assert "sk-or-sentinela-0027" not in sem_docker.stdout + sem_docker.stderr + sem_manager.stdout


def test_documentacao_e_ajuda_listam_os_mesmos_subcomandos(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 FR-001 FR-010 NFR-004 AC-018"""
    amb = Ambiente(tmp_path)
    guia = RAIZ / "deploy" / "SECRETS.md"

    assert guia.is_file(), "deploy/SECRETS.md ainda não existe"
    texto = guia.read_text(encoding="utf-8")
    ajuda = amb.secrets_script("--ajuda")
    regras = (RAIZ / ".specsfy" / "RULES.md").read_text(encoding="utf-8")

    assert ajuda.returncode == 0
    for subcomando in ("criar", "trocar", "verificar", "resolver"):
        assert subcomando in ajuda.stdout
        assert f"deploy/secrets.sh {subcomando}" in texto
    for tema in ("ALTER USER", "recadastrar", "gerenciador de senhas", "_v1", "_local_v1"):
        assert tema in texto
    assert "deploy/secrets.sh" in regras
