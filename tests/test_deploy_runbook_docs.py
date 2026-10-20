"""Runbook de deploy manual em produção (SPEC-0035).

Fase RED: `deploy/RUNBOOK.md` ainda não existe. O teste de contrato confere a ordem
dos passos, as citações a arquivos, flags, serviços e secrets, e a ausência de
segredo, domínio real e comando destrutivo.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
RUNBOOK = RAIZ / "deploy" / "RUNBOOK.md"
STACK = RAIZ / "deploy" / "stack.prod.yml"

SERVICO = re.compile(r"(?:rag-pipeline_)?([a-z0-9]+(?:_[a-z0-9]+)*_ragpipeline)\b")
DESTRUTIVOS = re.compile(
    r"migrate:(fresh|refresh|reset|rollback)|db:wipe|schema:drop|prisma migrate reset|"
    r"DROP\s+(DATABASE|SCHEMA|TABLE)|TRUNCATE|docker\s+volume\s+rm|docker\s+system\s+prune|"
    r"docker\s+stack\s+rm",
    re.IGNORECASE,
)


def _texto() -> str:
    assert RUNBOOK.exists(), "deploy/RUNBOOK.md ainda não existe"
    return RUNBOOK.read_text(encoding="utf-8")


def _secoes(texto: str, nivel: str) -> list[tuple[str, str]]:
    """Divide o texto em (título, corpo) pelos títulos do nível dado (`##` ou `###`)."""
    partes = re.split(rf"(?m)^{nivel} (.+)$", texto)
    return [(partes[i].strip().lower(), partes[i + 1]) for i in range(1, len(partes) - 1, 2)]


def _area(texto: str, parte_do_titulo: str) -> str:
    for titulo, corpo in _secoes(texto, "##"):
        if parte_do_titulo in titulo:
            return corpo
    raise AssertionError(f"área '{parte_do_titulo}' ausente no runbook")


def _subsecao(area: str, parte_do_titulo: str) -> str:
    for titulo, corpo in _secoes(area, "###"):
        if parte_do_titulo in titulo:
            return corpo
    raise AssertionError(f"passo '{parte_do_titulo}' ausente")


def _blocos_de_codigo(texto: str) -> list[str]:
    return re.findall(r"```[a-z]*\n(.*?)```", texto, flags=re.DOTALL)


def _linhas_de_comando(texto: str) -> list[str]:
    linhas = [linha for bloco in _blocos_de_codigo(texto) for linha in bloco.splitlines()]
    return linhas + re.findall(r"`([^`\n]+)`", texto)


def _servicos_e_secrets_do_stack() -> tuple[set[str], set[str]]:
    stack = yaml.safe_load(STACK.read_text(encoding="utf-8"))
    return set(stack["services"]), set(stack.get("secrets", {}))


def _citacoes_quebradas(texto: str) -> list[str]:
    """Citações do texto a arquivos, flags, subcomandos e serviços que não existem."""
    quebradas: list[str] = []
    servicos, _ = _servicos_e_secrets_do_stack()
    for comando in _linhas_de_comando(texto):
        for caminho in re.findall(r"deploy/[\w./-]*\w", comando):
            if not (RAIZ / caminho).exists():
                quebradas.append(f"arquivo {caminho}")
        script = re.search(r"(deploy/[\w/-]+\.sh)\b(.*)", comando)
        if script and (RAIZ / script.group(1)).exists():
            codigo = (RAIZ / script.group(1)).read_text(encoding="utf-8")
            for flag in re.findall(r"(?<!\S)(--[a-z][a-z-]*)", script.group(2)):
                if flag not in codigo:
                    quebradas.append(f"flag {flag} em {script.group(1)}")
            if script.group(1).endswith("secrets.sh"):
                sub = re.match(r"\s+([a-z]+)", script.group(2))
                if sub and sub.group(1) not in codigo:
                    quebradas.append(f"subcomando {sub.group(1)} em secrets.sh")
    for servico in set(SERVICO.findall(texto)):
        if servico not in servicos:
            quebradas.append(f"serviço {servico}")
    return quebradas


def test_documenta_as_tres_areas_em_passos_numerados() -> None:
    """SPECSFY: SPEC-0035 US-001 US-003 US-004 FR-001 NFR-003 AC-001"""
    texto = _texto()

    for parte in ("atualiz", "primeira instala", "emerg"):
        area = _area(texto, parte)
        assert (
            len(re.findall(r"(?m)^\d+\. ", area)) >= 3 or len(re.findall(r"(?m)^### ", area)) >= 3
        ), f"a área '{parte}' não traz passos numerados"


def test_atualizacao_segue_a_ordem_dos_passos() -> None:
    """SPECSFY: SPEC-0035 US-001 FR-002 FR-003 AC-002"""
    area = _area(_texto(), "atualiz")

    titulos = [titulo for titulo, _ in _secoes(area, "###")]
    posicoes = []
    for chave in ("pré-condi", "backup", "migra", "deploy", "verifica"):
        achados = [i for i, titulo in enumerate(titulos) if chave in titulo]
        assert achados, f"passo '{chave}' ausente na atualização"
        posicoes.append(achados[0])
    assert posicoes == sorted(posicoes)


def test_confere_lote_em_andamento_por_consulta_somente_de_leitura() -> None:
    """SPECSFY: SPEC-0035 US-001 FR-002 NFR-002 AC-003"""
    passo = _subsecao(_area(_texto(), "atualiz"), "pré-condi")

    minusculo = passo.lower()
    for termo in ("executions", "pending", "running", "select", "esper"):
        assert termo in minusculo
    codigo = "\n".join(_blocos_de_codigo(passo))
    assert not re.search(r"\b(insert|update|delete|drop|truncate|alter)\b", codigo, re.IGNORECASE)


def test_migracao_e_passo_separado_com_backup_antes() -> None:
    """SPECSFY: SPEC-0035 US-001 US-004 FR-002 FR-003 FR-008 AC-004"""
    area = _area(_texto(), "atualiz")

    passo = _subsecao(area, "migra").lower()
    assert "alembic upgrade head" in passo
    assert "backup" in passo
    assert "não atualize o serviço" in passo
    assert "restaur" in passo
    assert area.lower().index("### backup") < area.lower().index("### migra")


def test_verificacao_usa_o_script_de_dominio_e_a_lista_completa() -> None:
    """SPECSFY: SPEC-0035 US-001 US-003 FR-007 AC-010"""
    passo = _subsecao(_area(_texto(), "atualiz"), "verifica").lower()

    assert "deploy/conferir_dominio.sh" in passo
    assert "login" in passo and "assistente" in passo
    assert "lista completa" in passo
    assert "primeira instalação" in passo and "mudança grande" in passo


def test_primeira_instalacao_segue_a_ordem_e_fecha_com_a_lista_completa() -> None:
    """SPECSFY: SPEC-0035 US-003 FR-001 FR-003 FR-007 AC-011"""
    area = _area(_texto(), "primeira instala")

    marcos = [
        "deploy/secrets.sh criar",
        "domínio",
        "backup_chave",
        "alembic upgrade head",
        "deploy/build_and_deploy.sh",
        "lista completa",
    ]
    minusculo = area.lower()
    posicoes = [minusculo.index(marco) for marco in marcos]
    assert posicoes == sorted(posicoes)
    final = minusculo[posicoes[-1] :]
    for termo in ("pessoa", "base", "assistente"):
        assert termo in final


def test_emergencias_voltam_a_versao_e_apontam_a_restauracao() -> None:
    """SPECSFY: SPEC-0035 US-001 US-004 FR-006 FR-007 FR-008 AC-012"""
    area = _area(_texto(), "emerg")

    for termo in ("--versao", "docker service rollback", "deploy/BACKUP.md", "restaurar.sh"):
        assert termo in area


def test_nenhum_comando_destrutivo_de_banco_vira_passo() -> None:
    """SPECSFY: SPEC-0035 US-004 FR-008 NFR-002 AC-013"""
    texto = _texto()

    for linha in _linhas_de_comando(texto):
        assert not DESTRUTIVOS.search(linha), f"comando destrutivo no runbook: {linha}"
    assert "restaurar.sh" in texto


def test_nao_contem_segredo_nem_dominio_real() -> None:
    """SPECSFY: SPEC-0035 FR-001 FR-009 NFR-001 AC-014"""
    texto = _texto()

    assert not re.search(r"(AKIA[0-9A-Z]{8,}|-----BEGIN|(?i:password|senha)\s*=\s*\S+)", texto)
    for host in re.findall(r"https?://([^/\s`>)]+)", texto):
        assert host.startswith("<") or host.endswith(".invalid"), f"endereço real: {host}"
    assert "DOMINIO_RAGPIPELINE" in texto


def test_detecta_referencia_quebrada() -> None:
    """SPECSFY: SPEC-0035 US-001 FR-009 NFR-003 AC-015"""
    assert _citacoes_quebradas(_texto()) == []

    falso = (
        "Rode `deploy/nao_existe.sh` e `deploy/build_and_deploy.sh --flag-inexistente`, "
        "depois `deploy/secrets.sh subinexistente` no serviço `fantasma_ragpipeline`."
    )
    quebradas = _citacoes_quebradas(falso)
    assert len(quebradas) == 4, quebradas


def test_flags_e_subcomandos_citados_existem_nos_scripts() -> None:
    """SPECSFY: SPEC-0035 US-002 FR-009 AC-016"""
    texto = _texto()

    assert "deploy/build_and_deploy.sh --versao" in texto
    assert "--versao" in (RAIZ / "deploy" / "build_and_deploy.sh").read_text(encoding="utf-8")
    assert "deploy/secrets.sh criar" in texto
    assert "criar" in (RAIZ / "deploy" / "secrets.sh").read_text(encoding="utf-8")
    assert _citacoes_quebradas(texto) == []


def test_secrets_sao_criados_pela_entrada_padrao() -> None:
    """SPECSFY: SPEC-0035 NFR-001 AC-021"""
    texto = _texto()

    assert "entrada padrão" in texto.lower()
    comandos = [linha for linha in _linhas_de_comando(texto) if "deploy/secrets.sh" in linha]
    assert comandos, "o runbook não cita deploy/secrets.sh"
    for comando in comandos:
        assert not re.search(r"\S+=\S+", comando), f"valor na linha de comando: {comando}"
        assert "echo" not in comando and "--valor" not in comando


def test_delega_so_marca_o_que_mudaria() -> None:
    """SPECSFY: SPEC-0035 US-001 US-003 FR-001 AC-023"""
    texto = _texto().lower()

    assert "só a pessoa responsável" in texto
    assert "delegar" in texto
    for termo in ("acessos", "chaves", "registro de deploys"):
        assert termo in texto


def test_documentacao_descreve_os_servicos_externos_sem_valores_reais() -> None:
    """SPECSFY: SPEC-0041 US-001 FR-005 NFR-001 AC-011"""
    pasta = RAIZ / "deploy"
    texto = "\n".join(
        (pasta / nome).read_text(encoding="utf-8")
        for nome in ("RUNBOOK.md", "SECRETS.md", "BACKUP.md")
    )
    for termo in (
        "DATABASE_HOST",
        "DATABASE_SSLMODE",
        "QDRANT_URL",
        "qdrant_api_key",
        "APP_COLECAO_PREFIXO",
        "alembic upgrade head",
    ):
        assert termo in texto, f"falta documentar {termo}"
    assert "supabase.com" not in texto and "smartsystem" not in texto
    assert "postgres_ragpipeline" not in texto and "qdrant_ragpipeline" not in texto
