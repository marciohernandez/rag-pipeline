"""Testes do histórico de acessos e da limpeza de retenção (SPEC-0020, fase RED)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from tests._pessoas import (
    NOVA_SENHA,
    SENHA,
    cliente,
    consultar,
    criar_pessoa,
    entrar,
    eventos,
    login,
    pessoa_com_sessao,
    recurso,
    sessao_do_banco,
)

TIPOS = {
    "entrou",
    "senha_errada",
    "bloqueada",
    "senha_trocada",
    "senha_redefinida",
    "pessoa_criada",
    "dados_corrigidos",
    "papel_alterado",
    "pessoa_desativada",
    "pessoa_reativada",
    "sessao_encerrada",
}


def _provocar_todos_os_tipos(cli) -> dict[str, str]:
    _, sessao_dono = pessoa_com_sessao(cli, papel="owner")
    alvo = criar_pessoa()
    login(cli, alvo["email"], "senha-errada-123")
    for _ in range(5):
        login(cli, alvo["email"], "senha-errada-123")
    login(cli, alvo["email"], alvo["senha"])  # bloqueada
    base = f"/api/v1/pessoas/{alvo['id']}"
    cli.patch(base, json={"nome": "Corrigido"}, headers=sessao_dono)
    cli.patch(base, json={"papel": "admin"}, headers=sessao_dono)
    cli.post(f"{base}/desativar", headers=sessao_dono)
    cli.post(f"{base}/reativar", headers=sessao_dono)
    cli.post(
        f"{base}/redefinir-senha",
        json={"senha_temporaria": "senha-temporaria-123"},
        headers=sessao_dono,
    )
    cli.post(
        "/api/v1/pessoas",
        json={
            "nome": "Nova",
            "email": "nova-evento@exemplo.com",
            "papel": "member",
            "senha_inicial": "senha-inicial-123",
        },
        headers=sessao_dono,
    )
    outra = criar_pessoa()
    sessao_outra = entrar(cli, outra["email"], outra["senha"])
    cli.post(
        "/api/v1/auth/senha",
        json={"senha_atual": SENHA, "nova_senha": NOVA_SENHA},
        headers=sessao_outra,
    )
    return {"alvo": alvo["id"], "outra": outra["id"]}


def test_cada_evento_gera_registro_sem_segredo() -> None:
    """SPECSFY: SPEC-0020 US-006 FR-012 NFR-001 AC-018"""
    cli = cliente()
    _provocar_todos_os_tipos(cli)

    registrados = {evento.tipo for evento in consultar("EventoAcesso")}
    assert registrados >= TIPOS, f"faltam: {sorted(TIPOS - registrados)}"
    for evento in consultar("EventoAcesso"):
        assert evento.criado_em is not None
        texto = " ".join(str(valor) for valor in vars(evento).values())
        assert SENHA not in texto and NOVA_SENHA not in texto and "argon2" not in texto
    falhas = eventos("senha_errada")
    assert falhas and all(evento.ator_pessoa_id is None for evento in falhas)


def test_limpeza_apaga_eventos_com_mais_de_noventa_dias() -> None:
    """SPECSFY: SPEC-0020 US-006 FR-012 AC-019"""
    evento_modelo = recurso("src.app.models", "EventoAcesso")
    sessao_modelo = recurso("src.app.models", "Sessao")
    tentativa_modelo = recurso("src.app.models", "TentativaLogin")
    purgar = recurso("src.app.events", "purgar_dados_de_acesso")
    agora = datetime.now(UTC)
    dono = criar_pessoa()

    with sessao_do_banco() as sessao:
        recente = evento_modelo(tipo="entrou", criado_em=agora - timedelta(days=89))
        antigo = evento_modelo(tipo="entrou", criado_em=agora - timedelta(days=91))
        expirada = sessao_modelo(
            pessoa_id=dono["id"],
            token_hash="a" * 64,
            criada_em=agora - timedelta(hours=9),
            expira_em=agora - timedelta(hours=1),
        )
        valida = sessao_modelo(
            pessoa_id=dono["id"],
            token_hash="b" * 64,
            criada_em=agora,
            expira_em=agora + timedelta(hours=8),
        )
        vencida = tentativa_modelo(
            email_normalizado="vencida@exemplo.com",
            falhas_seguidas=5,
            bloqueada_ate=agora - timedelta(minutes=30),
        )
        ativa = tentativa_modelo(
            email_normalizado="ativa@exemplo.com",
            falhas_seguidas=5,
            bloqueada_ate=agora + timedelta(minutes=10),
        )
        sessao.add_all([recente, antigo, expirada, valida, vencida, ativa])
        sessao.commit()
        ids = {"recente": recente.id, "antigo": antigo.id}

    with sessao_do_banco() as sessao:
        primeira = purgar(sessao, agora)

    with sessao_do_banco() as sessao:
        segunda = purgar(sessao, agora)

    assert primeira == {"eventos": 1, "sessoes": 1, "tentativas": 1}
    assert segunda == {"eventos": 0, "sessoes": 0, "tentativas": 0}

    restantes = {evento.id for evento in consultar("EventoAcesso")}
    assert ids["recente"] in restantes
    assert ids["antigo"] not in restantes
    hashes = {s.token_hash for s in consultar("Sessao")}
    assert "b" * 64 in hashes and "a" * 64 not in hashes
    emails = {t.email_normalizado for t in consultar("TentativaLogin")}
    assert "ativa@exemplo.com" in emails and "vencida@exemplo.com" not in emails


def test_nenhum_segredo_em_resposta_log_ou_evento(caplog) -> None:
    """SPECSFY: SPEC-0020 US-001 US-006 FR-003 FR-012 NFR-001 AC-021"""
    cli = cliente()
    caplog.set_level(logging.DEBUG)
    pessoa = criar_pessoa()
    resposta_login = login(cli, pessoa["email"], pessoa["senha"])
    token = resposta_login.json()["token"]
    cabecalho = {"Authorization": f"Bearer {token}"}
    troca = cli.post(
        "/api/v1/auth/senha",
        json={"senha_atual": SENHA, "nova_senha": NOVA_SENHA},
        headers=cabecalho,
    )
    _, sessao_dono = pessoa_com_sessao(cli, papel="owner")
    redefinicao = cli.post(
        f"/api/v1/pessoas/{pessoa['id']}/redefinir-senha",
        json={"senha_temporaria": "senha-temporaria-123"},
        headers=sessao_dono,
    )

    respostas = " ".join(r.text for r in (troca, redefinicao))
    assert "argon2" not in respostas and "senha_hash" not in respostas
    assert NOVA_SENHA not in respostas and "senha-temporaria-123" not in respostas
    corpo_login = str(resposta_login.json())
    assert SENHA not in corpo_login and "argon2" not in corpo_login
    saida_de_log = " ".join(registro.getMessage() for registro in caplog.records)
    for segredo in (SENHA, NOVA_SENHA, "senha-temporaria-123", token):
        assert segredo not in saida_de_log
    texto_de_eventos = " ".join(
        str(valor) for evento in consultar("EventoAcesso") for valor in vars(evento).values()
    )
    for segredo in (SENHA, NOVA_SENHA, "senha-temporaria-123", token):
        assert segredo not in texto_de_eventos
