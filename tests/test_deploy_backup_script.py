"""Ciclo de backup do Postgres de produção (SPEC-0034).

Fase RED: `deploy/backup/backup.sh` ainda não existe. Os casos exercitam o script
real com `pg_dump`, `aws`, `curl` e demais binários falsos no `PATH`
(`tests/_backup_falso.py`); o `openssl` é o real.
"""

from __future__ import annotations

from pathlib import Path

from tests._backup_falso import (
    CHAVE,
    DUMP_EM_CLARO,
    SEGREDOS,
    AmbienteBackup,
    semana,
)

DOMINGO = "2026-10-18"
QUARTA = "2026-10-14"


def _datas(inicio: int, quantidade: int, mes: str = "2026-10") -> list[str]:
    return [f"{mes}-{dia:02d}" for dia in range(inicio, inicio + quantidade)]


def test_ciclo_gera_cifra_e_envia_o_dump_do_dia(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-001"""
    amb = AmbienteBackup(tmp_path)

    resultado = amb.backup(BACKUP_DATA=QUARTA)

    assert resultado.returncode == 0, resultado.stderr
    assert amb.objetos() == [f"diarios/{QUARTA}.dump.enc"]
    assert DUMP_EM_CLARO in amb.descriptografar(f"diarios/{QUARTA}.dump.enc").decode(
        errors="ignore"
    )
    chamadas_dump = amb.log("pg_dump")
    assert len(chamadas_dump) == 1 and "-Fc" in chamadas_dump[0]
    assert amb.log("docker") == [], "o ciclo não pode parar nem tocar nos serviços da aplicação"


def test_dump_em_claro_so_existe_no_diretorio_temporario_e_e_removido(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 FR-002 NFR-001 AC-002"""
    amb = AmbienteBackup(tmp_path)

    sucesso = amb.backup(BACKUP_DATA=QUARTA)
    assert sucesso.returncode == 0, sucesso.stderr
    assert list(amb.tmp.iterdir()) == []
    for chave in amb.objetos():
        assert chave.endswith(".enc"), chave
        assert DUMP_EM_CLARO.encode() not in (amb.bucket / chave).read_bytes()

    falha = amb.backup(BACKUP_DATA="2026-10-15", FAKE_AWS_FALHA_ENVIO="1")
    assert falha.returncode != 0
    assert list(amb.tmp.iterdir()) == []


def test_domingo_cria_a_copia_semanal_e_reexecutar_nao_duplica(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 FR-003 FR-005 NFR-004 AC-003"""
    amb = AmbienteBackup(tmp_path)

    quarta = amb.backup(BACKUP_DATA=QUARTA)
    assert quarta.returncode == 0, quarta.stderr
    assert amb.objetos("semanais/") == []

    for _ in range(2):
        domingo = amb.backup(BACKUP_DATA=DOMINGO)
        assert domingo.returncode == 0, domingo.stderr

    assert amb.objetos("semanais/") == [f"semanais/{semana(DOMINGO)}.dump.enc"]
    assert amb.objetos("diarios/") == [f"diarios/{QUARTA}.dump.enc", f"diarios/{DOMINGO}.dump.enc"]


def test_retencao_mantem_sete_diarios_e_quatro_semanais(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 FR-004 FR-005 NFR-002 AC-004"""
    amb = AmbienteBackup(tmp_path)
    diarios = _datas(11, 7)
    semanais = ["2026-S38", "2026-S39", "2026-S40", "2026-S41"]
    for dia in diarios:
        amb.semear(f"diarios/{dia}.dump.enc")
    for rotulo in semanais:
        amb.semear(f"semanais/{rotulo}.dump.enc")
    amb.semear("outros/anotacao.txt")

    resultado = amb.backup(BACKUP_DATA=DOMINGO)

    assert resultado.returncode == 0, resultado.stderr
    esperados_diarios = [f"diarios/{d}.dump.enc" for d in [*diarios[1:], DOMINGO]]
    esperados_semanais = [f"semanais/{r}.dump.enc" for r in [*semanais[1:], semana(DOMINGO)]]
    assert amb.objetos("diarios/") == esperados_diarios
    assert amb.objetos("semanais/") == esperados_semanais
    assert amb.objetos("outros/") == ["outros/anotacao.txt"]


def test_verificacao_aprova_tamanho_e_conteudo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 FR-002 FR-004 AC-005"""
    amb = AmbienteBackup(tmp_path)

    resultado = amb.backup(BACKUP_DATA=QUARTA)

    assert resultado.returncode == 0, resultado.stderr
    assert any(c.startswith("s3 ls ") for c in amb.log("aws")), "o tamanho remoto foi consultado"
    assert any("--list" in c or " -l " in f" {c} " for c in amb.log("pg_restore"))
    saida = resultado.stdout + resultado.stderr
    assert "verificar" in saida and "sucesso" in saida.lower()


def test_verificacao_reprovada_nao_poda_e_preserva_os_anteriores(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 US-002 FR-004 FR-005 NFR-002 AC-006"""
    for variacao in ({"FAKE_DUMP_BYTES": "0"}, {"FAKE_DUMP_INVALIDO": "1"}):
        base = tmp_path / ("vazio" if "FAKE_DUMP_BYTES" in variacao else "invalido")
        base.mkdir()
        amb = AmbienteBackup(base)
        for dia in _datas(7, 7):
            amb.semear(f"diarios/{dia}.dump.enc")
        antes = amb.objetos()

        resultado = amb.backup(BACKUP_DATA=QUARTA, **variacao)

        assert resultado.returncode != 0
        depois = amb.objetos()
        assert set(antes) <= set(depois), "nenhum backup anterior pode ser removido"
        assert "etapa=verificar" in amb.corpos()
        assert amb.log("curl_tipos") == ["smtp", "webhook"]


def test_bucket_indisponivel_repete_o_envio_e_avisa_ao_esgotar(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-001 US-002 FR-003 FR-006 NFR-002 AC-007"""
    amb = AmbienteBackup(tmp_path)
    amb.semear("diarios/2026-10-13.dump.enc")

    resultado = amb.backup(BACKUP_DATA=QUARTA, FAKE_AWS_FALHA_ENVIO="1")

    assert resultado.returncode != 0
    assert len(amb.envios()) == 3, "três tentativas de envio"
    assert amb.objetos() == ["diarios/2026-10-13.dump.enc"]
    assert sorted(amb.log("curl_tipos")) == ["smtp", "webhook"]
    assert "etapa=enviar" in amb.corpos()


def test_falha_avisa_por_email_e_por_chat_sem_segredos(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-002 FR-006 NFR-001 AC-008"""
    amb = AmbienteBackup(tmp_path)

    resultado = amb.backup(BACKUP_DATA=QUARTA, FAKE_PG_DUMP_FALHA="1")

    assert resultado.returncode != 0
    assert sorted(amb.log("curl_tipos")) == ["smtp", "webhook"]
    corpos = amb.corpos()
    assert "etapa=dump" in corpos
    assert "marcio@exemplo.invalid" in amb.log("curl_args")[0] or any(
        "marcio@exemplo.invalid" in c for c in amb.log("curl_args")
    )
    for segredo in SEGREDOS:
        assert segredo not in corpos
        assert segredo not in "\n".join(amb.log("curl_args"))


def test_falha_do_email_nao_impede_o_aviso_no_chat(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-002 FR-006 FR-009 AC-009"""
    amb = AmbienteBackup(tmp_path)

    resultado = amb.backup(BACKUP_DATA=QUARTA, FAKE_PG_DUMP_FALHA="1", FAKE_CURL_FALHA_SMTP="1")

    assert resultado.returncode != 0
    assert "webhook" in amb.log("curl_tipos")
    saida = (resultado.stdout + resultado.stderr).lower()
    assert "e-mail" in saida and "falh" in saida


def test_sucesso_nao_avisa_e_fica_so_no_log(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-002 FR-006 FR-009 AC-010"""
    amb = AmbienteBackup(tmp_path)

    resultado = amb.backup(BACKUP_DATA=QUARTA)

    assert resultado.returncode == 0, resultado.stderr
    assert amb.log("curl_tipos") == []
    saida = resultado.stdout + resultado.stderr
    assert QUARTA in saida
    assert "bytes" in saida
    assert "retenção" in saida or "retencao" in saida


def test_reexecutar_no_mesmo_dia_substitui_sem_duplicar(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 FR-001 FR-003 NFR-004 AC-017"""
    amb = AmbienteBackup(tmp_path)

    primeira = amb.backup(BACKUP_DATA=QUARTA)
    segunda = amb.backup(BACKUP_DATA=QUARTA)

    assert primeira.returncode == 0 and segunda.returncode == 0, segunda.stderr
    assert amb.objetos() == [f"diarios/{QUARTA}.dump.enc"]
    assert "substitu" in (segunda.stdout + segunda.stderr).lower()


def test_log_nao_expoe_segredos_e_termina_com_resumo(tmp_path: Path) -> None:
    """SPECSFY: SPEC-0034 US-002 FR-009 NFR-001 AC-020"""
    amb = AmbienteBackup(tmp_path)

    sucesso = amb.backup(BACKUP_DATA=QUARTA)
    falha = amb.backup(BACKUP_DATA="2026-10-15", FAKE_PG_DUMP_FALHA="1")

    vazamento = amb.tudo_que_vaza(sucesso, falha)
    for segredo in SEGREDOS:
        assert segredo not in vazamento, f"segredo exposto: {segredo[:12]}…"
    assert CHAVE not in vazamento
    for resultado in (sucesso, falha):
        linhas = [linha for linha in (resultado.stdout + resultado.stderr).splitlines() if linha]
        assert linhas[-1].startswith("RESUMO"), linhas[-1]
    saida = sucesso.stdout + sucesso.stderr
    for etapa in ("dump", "cifrar", "enviar", "verificar", "reter"):
        assert f"etapa={etapa}" in saida
