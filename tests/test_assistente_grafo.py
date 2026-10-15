"""Testes do grafo do assistente com modelo e recuperação de teste (SPEC-0021).

Contrato fixado: ``executar_turno(chat_model=, buscar_conhecimento=, historico=,
texto=, base=None)`` devolve um objeto com ``texto`` e ``fontes``. ``historico``
é a lista cronológica de mensagens da conversa (``papel``, ``conteudo``);
``buscar_conhecimento(pergunta)`` devolve trechos, lista vazia (sem suporte) ou
``None`` (coleção de conhecimento ausente).
"""

from __future__ import annotations

import re
from types import SimpleNamespace

from tests._assistente import ModeloDeTeste, exigir, resultado


def _turno(modelo, *, buscar, historico=None, texto="como funciona?", base=None):
    executar = exigir("src.pipeline.assistant", "executar_turno")
    return executar(
        chat_model=modelo,
        buscar_conhecimento=buscar,
        historico=historico or [],
        texto=texto,
        base=base,
    )


def _msg(papel: str, conteudo: str):
    return SimpleNamespace(papel=papel, conteudo=conteudo)


def _sistema(modelo) -> str:
    primeira = modelo.chamadas[-1][0]
    assert primeira.papel == "sistema"
    return primeira.conteudo


def test_resposta_usa_trechos_recuperados_e_devolve_as_fontes() -> None:
    """SPECSFY: SPEC-0021 US-003 FR-005 FR-006 AC-008"""
    trecho = "A ingestão lê o Markdown, aplica o chunker e faz upsert no Qdrant."
    modelo = ModeloDeTeste("Ele lê, divide e indexa.")
    resposta = _turno(
        modelo,
        buscar=lambda pergunta: [resultado(trecho, "docs/architecture.md")],
        texto="como o sistema processa um documento?",
    )
    assert trecho in modelo.contexto()
    assert resposta.texto == "Ele lê, divide e indexa."
    assert list(resposta.fontes) == ["docs/architecture.md"]


def test_sem_trechos_relevantes_instrui_o_modelo_a_admitir_lacuna() -> None:
    """SPECSFY: SPEC-0021 US-003 FR-005 FR-006 AC-009"""
    modelo = ModeloDeTeste()
    resposta = _turno(modelo, buscar=lambda pergunta: [], texto="o sistema exporta para PDF?")
    contexto = modelo.contexto().lower()
    assert re.search(r"não encontr", contexto), "o prompt deve mandar admitir que não encontrou"
    assert re.search(r"não (afirm|invent)", contexto), "o prompt deve proibir afirmar o recurso"
    assert list(resposta.fontes) == []


def test_prompt_de_sistema_restringe_escopo_e_nao_expoe_ferramentas() -> None:
    """SPECSFY: SPEC-0021 US-003 FR-006 FR-008 AC-010"""
    modelo = ModeloDeTeste()  # sem bind_tools: qualquer tentativa de expor ferramenta falha
    for pedido in ("crie uma Base chamada Vendas", "escreva um poema sobre o mar"):
        _turno(modelo, buscar=lambda pergunta: [], texto=pedido)
        sistema = _sistema(modelo).lower()
        assert "rag" in sistema and "pipeline" in sistema
        assert re.search(r"(apenas|somente) orient", sistema)
        assert re.search(r"recus", sistema)
    assert len(modelo.chamadas) == 2
    assert not hasattr(modelo, "bind_tools")


def test_mensagens_anteriores_da_conversa_entram_no_contexto() -> None:
    """SPECSFY: SPEC-0021 US-005 FR-003 FR-004 AC-014"""
    modelo = ModeloDeTeste()
    historico = [
        _msg("pessoa", "Tenho documentos em Markdown com seções longas."),
        _msg("assistente", "Então convém dividir por cabeçalhos."),
    ]
    _turno(
        modelo,
        buscar=lambda pergunta: [],
        historico=historico,
        texto="e o overlap ideal para isso?",
    )
    contexto = modelo.contexto()
    assert (
        contexto.index("seções longas")
        < contexto.index("dividir por cabeçalhos")
        < contexto.index("overlap ideal")
    )
    assert modelo.papeis()[-3:] == ["pessoa", "assistente", "pessoa"]


def test_contexto_nao_inclui_mensagens_de_outra_conversa() -> None:
    """SPECSFY: SPEC-0021 US-005 FR-004 NFR-001 AC-015"""
    modelo = ModeloDeTeste()
    conversa_a = [
        _msg("pessoa", "assunto-da-conversa-A"),
        _msg("assistente", "resposta-da-conversa-A"),
    ]
    conversa_b = [
        _msg("pessoa", "assunto-da-conversa-B"),
        _msg("assistente", "resposta-da-conversa-B"),
    ]
    _turno(modelo, buscar=lambda pergunta: [], historico=conversa_b, texto="continuando a B")
    contexto = modelo.contexto()
    assert "conversa-B" in contexto
    assert "conversa-A" not in contexto
    assert conversa_a[0].conteudo == "assunto-da-conversa-A"  # a outra conversa segue intacta


def test_contexto_limita_a_janela_de_vinte_mensagens() -> None:
    """SPECSFY: SPEC-0021 US-005 FR-004 NFR-002 AC-016"""
    modelo = ModeloDeTeste()
    historico = [
        _msg("pessoa" if i % 2 else "assistente", f"mensagem-numero-{i:02d}") for i in range(1, 31)
    ]
    copia = list(historico)
    _turno(modelo, buscar=lambda pergunta: [], historico=historico, texto="pergunta-seguinte")
    contexto = modelo.contexto()
    for i in range(11, 31):
        assert f"mensagem-numero-{i:02d}" in contexto
    for i in range(1, 11):
        assert f"mensagem-numero-{i:02d}" not in contexto
    assert historico == copia and len(historico) == 30


def test_colecao_de_conhecimento_ausente_avisa_e_ainda_orienta() -> None:
    """SPECSFY: SPEC-0021 FR-011 FR-005 AC-021"""
    modelo = ModeloDeTeste("Em RAG geral, prefira dividir por estrutura.")
    resposta = _turno(modelo, buscar=lambda pergunta: None, texto="qual splitter usar?")
    contexto = modelo.contexto().lower()
    assert re.search(r"não está disponível", contexto)
    assert re.search(r"conhecimento geral", contexto)
    assert resposta.texto == "Em RAG geral, prefira dividir por estrutura."
    assert list(resposta.fontes) == []


def _colecao_apontada(trechos):
    return {
        "nome": "Manuais",
        "documentos": ["manual.md"],
        "buscar": lambda pergunta: trechos,
    }


def test_colecao_apontada_autoriza_responder_sobre_o_conteudo_dela() -> None:
    """SPECSFY: FIX-ASSISTENTE-COLECAO prompt não pode recusar perguntas sobre a coleção"""
    modelo = ModeloDeTeste()
    _turno(
        modelo,
        buscar=lambda pergunta: [],
        base=_colecao_apontada([resultado("A garantia do modelo X dura 24 meses.", "manual.md")]),
        texto="qual a garantia do modelo X?",
    )
    sistema = _sistema(modelo).lower()
    # A regra "somente RAG" vale para o assunto geral; sobre a coleção apontada o
    # modelo deve ser autorizado explicitamente a responder pelo conteúdo.
    assert re.search(r"coleção apontada|conteúdo da coleção", sistema)
    assert re.search(r"responda.*(conteúdo|trechos).*(coleção|base)", sistema, re.DOTALL)


def test_fontes_incluem_os_documentos_dos_trechos_da_colecao() -> None:
    """SPECSFY: FIX-ASSISTENTE-COLECAO fontes citam os documentos da coleção apontada"""
    trecho = resultado("A garantia do modelo X dura 24 meses.", "manual.md")
    trecho.metadata["nome_arquivo"] = "manual.md"
    resposta = _turno(
        ModeloDeTeste(),
        buscar=lambda pergunta: [],
        base=_colecao_apontada([trecho]),
        texto="qual a garantia do modelo X?",
    )
    assert "manual.md" in list(resposta.fontes)


def _turno_copilot(modelo, *, texto, colecoes, estado, processado):
    """Roda o grafo com os três recuperadores da SPEC-0031 (contrato: ``pergunta -> lista``)."""
    import inspect

    executar = exigir("src.pipeline.assistant", "executar_turno")
    parametros = inspect.signature(executar).parameters
    for nome in ("colecoes", "estado", "processado"):
        if nome not in parametros:
            raise AssertionError(f"executar_turno ainda não aceita `{nome}` (SPEC-0031 ausente)")
    return executar(
        chat_model=modelo,
        buscar_conhecimento=lambda pergunta: [],
        historico=[],
        texto=texto,
        colecoes=colecoes,
        estado=estado,
        processado=processado,
    )


def test_sem_base_o_copilot_admite_que_nao_encontrou() -> None:
    """SPECSFY: SPEC-0031 US-004 FR-002 FR-009 NFR-002 NFR-003 AC-011"""
    from tests._copilot import ModeloCopilot

    modelo = ModeloCopilot()
    resposta = _turno_copilot(
        modelo,
        texto="qual é a política de viagens da empresa?",
        colecoes=lambda pergunta: [],
        estado=lambda pergunta: [],
        processado=lambda pergunta: [],
    )

    contexto = modelo.contexto().lower()
    assert re.search(r"não encontr", contexto), "o prompt deve mandar admitir que não encontrou"
    assert re.search(r"não (afirm|invent)", contexto), "o prompt deve proibir afirmar sem base"
    assert list(resposta.fontes) == []


def test_assunto_fora_do_produto_e_recusado_sem_busca() -> None:
    """SPECSFY: SPEC-0031 US-001 FR-002 FR-009 AC-016"""
    from tests._copilot import CLASSIFICAR, ModeloCopilot

    modelo = ModeloCopilot(classificacao="nenhuma")
    chamadas: list[str] = []

    def espiao(nome):
        return lambda pergunta: chamadas.append(nome) or []

    resposta = _turno_copilot(
        modelo,
        texto="escreva um poema sobre o mar",
        colecoes=espiao("colecoes"),
        estado=espiao("estado"),
        processado=espiao("processado"),
    )

    assert chamadas == []
    assert len(modelo.classificacoes) == 1
    assert modelo.classificacoes[0][0].conteudo.lstrip().startswith(CLASSIFICAR)
    assert "só pode ajudar" in modelo.contexto().lower() or "recuse" in modelo.contexto().lower()
    assert resposta.texto == modelo.resposta
