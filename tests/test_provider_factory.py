"""TDD informado pelo BDD da SPEC-0003 — seção 6.

AC-001: a mesma factory cria cada provider suportado e devolve um adapter que
satisfaz o contrato da sua família, sem que o consumidor conheça o SDK.
AC-002: nome, configuração ou credencial inválida gera o erro local específico
antes de qualquer cliente remoto.

Enquanto ``src/providers/`` não existir, cada caso falha por comportamento
ausente (``ModuleNotFoundError``). Nenhum código de produção é escrito nesta
fase.
"""

from __future__ import annotations

import pytest

EMBEDDING_CONTRACT = ("embed_documents", "embed_query")
VECTOR_STORE_CONTRACT = ("ensure_ready", "list_ids", "upsert", "query", "capabilities")

EMBEDDING_PROVIDERS = {
    "openai": {"model": "text-embedding-3-small", "api_key": "sk-teste", "dimensions": 8},
    "openrouter": {
        "model": "openai/text-embedding-3-small",
        "api_key": "sk-or-teste",
        "dimensions": 8,
    },
    "huggingface": {"model": "sentence-transformers/all-MiniLM-L6-v2"},
    "fake": {"dimensions": 8},
}

VECTOR_STORE_PROVIDERS = {
    "qdrant": {"collection_name": "conformidade", "url": "http://localhost:6333"},
    "chroma": {"collection_name": "conformidade", "persist_directory": "/tmp/none"},
    "pinecone": {"index_name": "conformidade", "namespace": "ns", "api_key": "pc-teste"},
    "in_memory": {},
}

MIRROR_CAPABLE = {"qdrant", "in_memory"}


# ─────────────────────────────────────────────
# AC-001 — Factory e adapters substituíveis
# ─────────────────────────────────────────────


@pytest.mark.parametrize("name", sorted(EMBEDDING_PROVIDERS))
def test_factory_cria_cada_adapter_de_embeddings_pelo_nome(name) -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-003 NFR-004 AC-001
    from src.providers.factory import ProviderFactory

    adapter = ProviderFactory.create_embedding(name, EMBEDDING_PROVIDERS[name])

    for method in EMBEDDING_CONTRACT:
        assert callable(getattr(adapter, method)), f"{name} não implementa {method}"


@pytest.mark.parametrize("name", sorted(VECTOR_STORE_PROVIDERS))
def test_factory_cria_cada_adapter_de_vector_store_pelo_nome(name) -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-003 NFR-004 AC-001
    from src.providers.factory import ProviderFactory

    adapter = ProviderFactory.create_vector_store(name, VECTOR_STORE_PROVIDERS[name])

    for method in VECTOR_STORE_CONTRACT:
        assert callable(getattr(adapter, method)), f"{name} não implementa {method}"


@pytest.mark.parametrize("name", sorted(VECTOR_STORE_PROVIDERS))
def test_extensao_mirror_existe_somente_nos_adapters_capazes(name) -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-003 NFR-004 AC-001
    from src.providers.factory import ProviderFactory

    adapter = ProviderFactory.create_vector_store(name, VECTOR_STORE_PROVIDERS[name])

    tem_delete_ids = callable(getattr(adapter, "delete_ids", None))
    assert adapter.capabilities().supports_mirror is (name in MIRROR_CAPABLE)
    assert tem_delete_ids is (name in MIRROR_CAPABLE)


def test_factory_despacha_somente_pelo_nome_sem_depender_de_segredo() -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-003 NFR-004 AC-001
    from src.providers.factory import ProviderFactory

    qdrant = ProviderFactory.create_vector_store("qdrant", VECTOR_STORE_PROVIDERS["qdrant"])
    chroma = ProviderFactory.create_vector_store("chroma", VECTOR_STORE_PROVIDERS["chroma"])

    assert type(qdrant) is not type(chroma)


# ─────────────────────────────────────────────
# AC-002 — Erros locais antes de acesso remoto
# ─────────────────────────────────────────────


def test_nome_desconhecido_gera_unknown_provider_error() -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-002
    from src.providers.errors import ProviderError, UnknownProviderError
    from src.providers.factory import ProviderFactory

    with pytest.raises(UnknownProviderError) as excinfo:
        ProviderFactory.create_embedding("inexistente", {})
    assert isinstance(excinfo.value, ProviderError)

    with pytest.raises(UnknownProviderError):
        ProviderFactory.create_vector_store("inexistente", {})


def test_configuracao_incompleta_gera_invalid_provider_config_error() -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-002
    from src.providers.errors import InvalidProviderConfigError, ProviderError
    from src.providers.factory import ProviderFactory

    with pytest.raises(InvalidProviderConfigError) as excinfo:
        ProviderFactory.create_vector_store("pinecone", {"api_key": "pc-teste"})
    assert isinstance(excinfo.value, ProviderError)


def test_credencial_obrigatoria_ausente_gera_missing_credential_error(monkeypatch) -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-002
    from src.providers.errors import MissingCredentialError, ProviderError
    from src.providers.factory import ProviderFactory

    # `src/config.py` chama `load_dotenv()` no import, então qualquer teste que
    # importe a configuração injeta a credencial do `.env` no processo. A regra
    # provada aqui é a ausência de credencial: garanta-a no próprio caso.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(MissingCredentialError) as excinfo:
        ProviderFactory.create_embedding("openai", {"model": "text-embedding-3-small"})
    assert isinstance(excinfo.value, ProviderError)


def test_erro_local_impede_qualquer_cliente_remoto() -> None:
    # SPECSFY: US-001 FR-001 FR-002 FR-003 NFR-001 NFR-003 AC-002
    from src.providers.errors import InvalidProviderConfigError
    from src.providers.factory import ProviderFactory

    # ``ensure_ready``/``query`` são os únicos pontos que abrem cliente remoto.
    # Um adapter só é devolvido quando a validação local passa; configuração
    # inválida encerra em ``create_*`` sem instanciar cliente.
    with pytest.raises(InvalidProviderConfigError):
        ProviderFactory.create_vector_store("qdrant", {"url": "não-é-uma-url"})
