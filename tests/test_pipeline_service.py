"""Testes TDD da SPEC-0008 — fronteira interna entre pipeline e backend.

Cada caso é derivado de um cenário BDD da seção 6 da spec e recebe um marcador
``SPECSFY:`` próprio. Os cenários de fronteira estática vivem em
``tests/test_application_boundaries.py``; os documentais em
``tests/test_docs_safety.py`` e ``tests/test_ci_gates.py``.

Enquanto a migração (T014) e a fachada (T015) não existirem, os casos que
importam ``src.pipeline`` falham por comportamento ausente — esse é o RED
esperado da fase 1.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

MODULOS_MIGRADOS = (
    "loader",
    "chunker",
    "identity",
    "manifest",
    "quality",
    "validation",
    "safety",
    "indexing",
    "exporter",
    "status_gate",
    "config",
    "providers",
)

ENTRYPOINTS_DE_OPERACAO = (
    "pipeline.py",
    "search.py",
    "chat.py",
    "validate.py",
    "upsert_from_chunks.py",
)

OPERACOES_DA_FACHADA = (
    "run_pipeline",
    "sync_vector_store",
    "validate_retrieval",
    "query_base",
)


def _fachada():
    """Importa a fachada; ausência dela é o RED da fatia."""
    return importlib.import_module("src.pipeline.service")


def _texto(nome: str) -> str:
    return (RAIZ / nome).read_text(encoding="utf-8")


# SPECSFY: US-002 FR-001 FR-002 NFR-001 AC-001
def test_pacote_migrado_para_src_pipeline_e_importavel() -> None:
    faltando = []
    for nome in MODULOS_MIGRADOS:
        try:
            importlib.import_module(f"src.pipeline.{nome}")
        except ModuleNotFoundError:
            faltando.append(nome)
    assert faltando == [], f"src/pipeline/ não expõe: {faltando}"
    assert (RAIZ / "src" / "app" / "__init__.py").is_file()


# SPECSFY: US-002 FR-001 FR-005 NFR-001 AC-002
def test_entrypoints_da_raiz_importam_de_src_pipeline() -> None:
    ofensores: dict[str, list[str]] = {}
    for nome in ENTRYPOINTS_DE_OPERACAO:
        texto = _texto(nome)
        internos = re.findall(r"from src\.(?!pipeline\b)(\w+)", texto)
        if internos or "src.pipeline" not in texto:
            ofensores[nome] = sorted(set(internos)) or ["sem import de src.pipeline"]
    assert ofensores == {}, f"entrypoints ainda acoplados ao interior: {ofensores}"


# SPECSFY: US-001 FR-003 FR-004 NFR-004 AC-003
def test_fachada_executa_com_configuracao_em_memoria(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)  # nenhum config.yaml acessível
    servico = _fachada()
    operacao = servico.sync_vector_store
    config = {
        "projeto": {"nome": "base-de-teste"},
        "embedding": {"provider": "fake"},
        "vector_store": {"provider": "fake"},
    }
    resultado = operacao(config=config, chunks=[])
    assert resultado is not None


# SPECSFY: US-001 FR-003 FR-004 NFR-002 AC-004
def test_fachada_recusa_configuracao_incompleta_sem_expor_credencial() -> None:
    servico = _fachada()
    operacao = servico.sync_vector_store
    with pytest.raises((KeyError, ValueError)) as capturado:
        operacao(config={}, chunks=[])
    mensagem = str(capturado.value).lower()
    assert "projeto" in mensagem or "chave" in mensagem
    assert "sk-" not in mensagem and "api_key" not in mensagem


# SPECSFY: US-001 FR-004 NFR-002 NFR-003 AC-007
def test_fachada_nao_le_disco_nem_ambiente_para_configuracao(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RAG_PROJECT", raising=False)
    servico = _fachada()
    fonte = Path(servico.__file__).read_text(encoding="utf-8")
    assert "load_config(" not in fonte, "a fachada não pode ler config.yaml"
    assert "os.getenv" not in fonte and "os.environ" not in fonte, (
        "a fachada não consulta ambiente para configuração não sensível"
    )
    assert "load_dotenv" not in fonte


# SPECSFY: US-001 FR-003 NFR-004 AC-008
def test_sincronizacao_devolve_as_quatro_contagens_no_retorno(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    servico = _fachada()
    operacao = servico.sync_vector_store
    config = {
        "projeto": {"nome": "base-de-teste"},
        "embedding": {"provider": "fake"},
        "vector_store": {"provider": "fake"},
    }
    resultado = operacao(config=config, chunks=[])
    for contagem in ("previstos", "inseridos", "mantidos", "removidos"):
        assert hasattr(resultado, contagem) or contagem in resultado


# SPECSFY: US-002 FR-004 FR-005 NFR-004 AC-011
def test_entrypoint_resolve_config_yaml_e_repassa_para_a_fachada() -> None:
    ofensores = []
    for nome in ENTRYPOINTS_DE_OPERACAO:
        texto = _texto(nome)
        resolve_config = "load_config(" in texto or "config.yaml" in texto
        chama_fachada = "src.pipeline.service" in texto or re.search(
            r"\bservice\.(run_pipeline|sync_vector_store|validate_retrieval|query_base)\b",
            texto,
        )
        if not (resolve_config and chama_fachada):
            ofensores.append(nome)
    assert ofensores == [], (
        f"entrypoints que não resolvem config e delegam à fachada: {ofensores}"
    )
