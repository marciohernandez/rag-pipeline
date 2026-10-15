import os
import stat
import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "deploy" / "build_and_deploy.sh"


def _docker_fake_que_falha_no_build(tmp_path: Path) -> tuple[Path, Path]:
    log = tmp_path / "chamadas.log"
    fake = tmp_path / "docker"
    fake.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$@" >> "{log}"\n'
        'if [ "$1" = "info" ]; then echo true; exit 0; fi\n'
        'if [ "$1 $2" = "secret ls" ]; then\n'
        "  printf '%s\\n' openrouter_api_key_v1 r2_credentials_v1 \\\n"
        "    postgres_password_v1 conexoes_chave_v1 backup_chave_v1 "
        "backup_r2_credentials_v1 backup_avisos_v1\n"
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "build" ]; then exit 1; fi\n'
        "exit 0\n"
    )
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    return fake, log


def test_build_falho_impede_execucao_do_deploy(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0022 US-001 FR-001 FR-002 NFR-001 AC-003"""
    _, log = _docker_fake_que_falha_no_build(tmp_path)
    # SPEC-0035: o deploy recusa árvore suja; um `git` falso isola o teste do repositório.
    git = tmp_path / "git"
    git.write_text('#!/usr/bin/env bash\n[ "$1" = rev-parse ] && echo abc1234\nexit 0\n')
    git.chmod(git.stat().st_mode | stat.S_IEXEC)
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["DOMINIO_RAGPIPELINE"] = "app-teste.invalid"

    resultado = subprocess.run(
        [str(SCRIPT_PATH)],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode != 0
    chamadas = log.read_text() if log.exists() else ""
    assert any(linha.startswith("build ") for linha in chamadas.splitlines())
    assert "stack deploy" not in chamadas


# --- SPEC-0027: verificação dos secrets antes dos builds -----------------------

from tests._docker_falso import Ambiente, todos_os_secrets


def test_secret_ausente_bloqueia_o_deploy_antes_dos_builds(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-004 AC-007"""
    secrets = todos_os_secrets()
    del secrets["conexoes_chave_v1"]
    amb = Ambiente(tmp_path, secrets)

    resultado = amb.deploy()

    assert resultado.returncode != 0
    texto = resultado.stdout + resultado.stderr
    assert "conexoes_chave" in texto
    assert "deploy/secrets.sh criar conexoes_chave" in texto
    chamadas = "\n".join(amb.chamadas())
    assert "build" not in chamadas
    assert "stack deploy" not in chamadas


def test_deploy_entrega_a_versao_resolvida_ao_stack(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 FR-005 FR-006 FR-007 AC-008"""
    secrets = todos_os_secrets({"openrouter_api_key": 2})
    secrets["openrouter_api_key_v1"] = "valor-antigo"
    amb = Ambiente(tmp_path, secrets)

    resultado = amb.deploy()

    assert resultado.returncode == 0, resultado.stderr
    ambiente_do_deploy = amb.ambiente_do_deploy()
    assert "OPENROUTER_API_KEY_SECRET=openrouter_api_key_v2" in ambiente_do_deploy
    assert "R2_CREDENTIALS_SECRET=r2_credentials_v1" in ambiente_do_deploy
    assert "POSTGRES_PASSWORD_SECRET=postgres_password_v1" in ambiente_do_deploy
    assert "CONEXOES_CHAVE_SECRET=conexoes_chave_v1" in ambiente_do_deploy
    assert "BACKUP_CHAVE_SECRET=backup_chave_v1" in ambiente_do_deploy
    assert "BACKUP_R2_CREDENTIALS_SECRET=backup_r2_credentials_v1" in ambiente_do_deploy
    assert "BACKUP_AVISOS_SECRET=backup_avisos_v1" in ambiente_do_deploy
    assert amb.criacoes() == []


def test_verificacao_vem_antes_dos_builds_e_o_deploy_por_ultimo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0027 US-002 FR-005 FR-006 NFR-002 AC-019"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy()
    chamadas = amb.chamadas()

    assert resultado.returncode == 0, resultado.stderr

    def posicao(prefixo: str) -> int:
        return next((i for i, c in enumerate(chamadas) if c.startswith(prefixo)), -1)

    primeira_listagem, primeiro_build, deploy = (
        posicao("secret ls"),
        posicao("build"),
        posicao("stack deploy"),
    )
    assert primeira_listagem >= 0, "a verificação dos secrets não consultou o Swarm"
    assert primeira_listagem < primeiro_build < deploy
    # SPEC-0035: depois do deploy só a poda de imagens antigas pode rodar.
    depois = [c.removeprefix("--context dados-teste ") for c in chamadas[deploy + 1 :]]
    assert all(c.startswith("image ") for c in depois)
    assert amb.criacoes() == []

    falho = Ambiente(tmp_path / "falho", todos_os_secrets()).deploy(FAKE_FALHAR_BUILD="1")
    assert falho.returncode != 0


# --- SPEC-0032: domínio obrigatório no deploy -------------------------------------


from tests._docker_falso import RAIZ


def test_deploy_sem_dominio_e_recusado_antes_de_build_e_stack_deploy(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0032 US-001 FR-001 NFR-001 AC-003"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    env = amb.env(DATABASE_NODE_HOSTNAME="no-de-dados", APPLICATION_NODE_HOSTNAME="no-de-aplicacao")
    assert "DOMINIO_RAGPIPELINE" not in env

    resultado = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        env=env,
        cwd=RAIZ,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert resultado.returncode != 0
    assert "DOMINIO_RAGPIPELINE" in resultado.stdout + resultado.stderr
    chamadas = "\n".join(amb.chamadas())
    assert "build" not in chamadas
    assert "stack deploy" not in chamadas


def test_backup_e_construido_no_contexto_do_no_de_dados(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-004 FR-008 NFR-003 AC-015"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy()

    assert resultado.returncode == 0, resultado.stderr
    chamadas = amb.chamadas()
    build = next(c for c in chamadas if "deploy/backup/Dockerfile" in c)
    assert build.startswith("--context dados-teste build ")
    assert chamadas.index(build) < next(
        i for i, chamada in enumerate(chamadas) if chamada.startswith("stack deploy")
    )


def test_contexto_de_backup_incorreto_bloqueia_o_deploy(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-004 FR-008 NFR-003 AC-015"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy(FAKE_NODE_NAME="outro-no")

    assert resultado.returncode != 0
    assert "não aponta para o nó de dados" in resultado.stderr
    assert not any("stack deploy" in chamada for chamada in amb.chamadas())


def test_backup_no_mesmo_no_dispensa_contexto_remoto(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-004 FR-008 NFR-003 AC-015"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy(APPLICATION_NODE_HOSTNAME="no-de-dados", BACKUP_DOCKER_CONTEXT="")

    assert resultado.returncode == 0, resultado.stderr
    build = next(c for c in amb.chamadas() if "deploy/backup/Dockerfile" in c)
    assert build.startswith("build ")


# --- SPEC-0035: versão por imagem, poda e volta atrás ----------------------------

import re

from tests._docker_falso import REPOSITORIOS


def _stack_producao() -> str:
    return (RAIZ / "deploy" / "stack.prod.yml").read_text(encoding="utf-8")


def test_cada_imagem_e_etiquetada_pela_versao_do_commit(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-004 AC-005"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy(FAKE_GIT_VERSAO="abc1234")

    assert resultado.returncode == 0, resultado.stderr
    chamadas = "\n".join(amb.chamadas())
    for repo in REPOSITORIOS:
        assert f"-t {repo}:abc1234" in chamadas
    assert amb.versoes_implantadas() == ["VERSAO_IMAGEM=abc1234"]
    stack = _stack_producao()
    for repo in REPOSITORIOS:
        assert f"{repo}:${{VERSAO_IMAGEM}}" in stack
        assert f"{repo}:local" not in stack


def test_arvore_suja_e_recusada_antes_de_qualquer_build(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-004 NFR-003 AC-006"""
    amb = Ambiente(tmp_path, todos_os_secrets())

    resultado = amb.deploy(FAKE_GIT_SUJO="1")

    assert resultado.returncode != 0
    texto = (resultado.stdout + resultado.stderr).lower()
    assert "commit" in texto
    chamadas = "\n".join(amb.chamadas())
    assert "build" not in chamadas
    assert "stack deploy" not in chamadas


def test_guarda_as_tres_ultimas_versoes_de_cada_imagem(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-005 AC-007"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    amb.semear_imagens(["v1", "v2", "v3", "v4", "v5"])

    resultado = amb.deploy(FAKE_GIT_VERSAO="abc1234")

    assert resultado.returncode == 0, resultado.stderr
    for repo in REPOSITORIOS:
        assert amb.etiquetas(repo) == ["abc1234", "v5", "v4"]


def test_volta_atras_reimplanta_uma_versao_guardada_sem_construir(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-006 AC-008"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    amb.semear_imagens(["v1", "v2", "v3"], em_uso="v3")

    resultado = amb.deploy("--versao", "v2")

    assert resultado.returncode == 0, resultado.stderr
    chamadas = amb.chamadas()
    assert not any(" build " in f" {c} " for c in chamadas)
    assert any(c.startswith("secret ls") for c in chamadas)
    assert amb.versoes_implantadas() == ["VERSAO_IMAGEM=v2"]


def test_versao_inexistente_e_recusada_com_a_lista_das_disponiveis(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-006 NFR-003 AC-009"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    amb.semear_imagens(
        ["v1", "v2", "v3"], repositorios=("rag-pipeline-backend", "rag-pipeline-backup")
    )
    with (amb.estado / "imagens.txt").open("a") as arquivo:
        arquivo.write("rag-pipeline-frontend:v1\nrag-pipeline-frontend:v3\n")

    faltando_em_uma = amb.deploy("--versao", "v2")
    inexistente = amb.deploy("--versao", "zzz")

    for resultado in (faltando_em_uma, inexistente):
        assert resultado.returncode != 0
        texto = resultado.stdout + resultado.stderr
        assert "v1" in texto and "v3" in texto
    assert "zzz" in inexistente.stdout + inexistente.stderr
    chamadas = "\n".join(amb.chamadas())
    assert "stack deploy" not in chamadas
    assert amb.versoes_implantadas() == []


def test_saidas_do_script_nao_repetem_segredos(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 FR-004 NFR-001 AC-017"""
    sentinela = "SENTINELA-SEGREDO-0035"
    secrets = {nome: f"{sentinela}-{nome}" for nome in todos_os_secrets()}
    cenarios = [
        ({"FAKE_GIT_VERSAO": "abc1234"}, ()),
        ({"FAKE_GIT_VERSAO": "abc1234", "FAKE_FALHAR_BUILD": "1"}, ()),
        ({"FAKE_GIT_VERSAO": "abc1234", "FAKE_GIT_SUJO": "1"}, ()),
        ({"FAKE_GIT_VERSAO": "abc1234"}, ("--versao", "zzz")),
    ]

    for numero, (env, args) in enumerate(cenarios):
        amb = Ambiente(tmp_path / f"cenario{numero}", secrets)
        resultado = amb.deploy(*args, OPENROUTER_API_KEY=f"{sentinela}-ambiente", **env)
        saida = resultado.stdout + resultado.stderr + "\n".join(amb.chamadas())
        assert sentinela not in saida
        if numero == 0:
            assert resultado.returncode == 0, resultado.stderr
            assert "abc1234" in resultado.stdout


def test_nada_e_podado_quando_o_deploy_falha(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-005 NFR-002 AC-018"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    amb.semear_imagens(["v1", "v2", "v3", "v4", "v5"])

    resultado = amb.deploy(FAKE_GIT_VERSAO="abc1234", FAKE_FALHAR_DEPLOY="1")

    assert resultado.returncode != 0
    assert amb.removidas() == []
    for repo in REPOSITORIOS:
        assert {"abc1234", "v1", "v2", "v3", "v4", "v5"} <= set(amb.etiquetas(repo))


def test_poda_preserva_a_versao_em_uso_e_a_de_retorno(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 US-002 FR-005 FR-006 AC-019"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    amb.semear_imagens(["v1", "v2", "v3", "v4", "v5", "v6"], em_uso="v1")

    resultado = amb.deploy(FAKE_GIT_VERSAO="abc1234")

    assert resultado.returncode == 0, resultado.stderr
    for repo in REPOSITORIOS:
        etiquetas = amb.etiquetas(repo)
        assert {"abc1234", "v6", "v5", "v1"} == set(etiquetas)
        assert not {"v2", "v3", "v4"} & set(etiquetas)


def test_poda_so_alcanca_etiquetas_antigas_das_imagens_do_projeto(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0035 NFR-002 AC-022"""
    amb = Ambiente(tmp_path, todos_os_secrets())
    extras = ["postgres:16-alpine", "outra-imagem:1", "qdrant/qdrant:v1.10.1"]
    amb.semear_imagens(["v1", "v2", "v3", "v4", "v5"], extras=extras)

    resultado = amb.deploy(FAKE_GIT_VERSAO="abc1234")

    assert resultado.returncode == 0, resultado.stderr
    assert amb.removidas(), "a poda não removeu nenhuma etiqueta antiga"
    for removida in amb.removidas():
        assert re.match(r"^rag-pipeline-(backend|frontend|backup):v\d+$", removida)
    restantes = (amb.estado / "imagens.txt").read_text().splitlines()
    for extra in extras:
        assert extra in restantes
    for chamada in amb.chamadas():
        assert not re.match(r"^(volume|network|system|container)\b", chamada)
        assert "image prune" not in chamada
