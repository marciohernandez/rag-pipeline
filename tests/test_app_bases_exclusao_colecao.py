"""Exclusão de Base usa a coleção e as conexões da própria Base (SPEC-0028).

Fase RED: ``apagar_base`` monta o vector store com a configuração global e sem a
coleção da Base, e ``service.delete_scope`` trata o 404 de coleção ausente como
falha de leitura. O vector store é substituído por um destino falso que registra
a configuração recebida (URL, chave e coleção) e guarda pontos por escopo, sem
rede e sem tocar o banco de desenvolvimento.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from fastapi.testclient import TestClient

from tests._conexoes import (
    CHAVE_QDRANT,
    OWNER,
    cliente,
    criar_conexao_ok,
    payload_embeddings,
    payload_qdrant,
    storage_temporario,
)
from tests._pessoas import sessao_do_banco

PADRAO = "rag-pipeline-app"
URL_GLOBAL = "http://qdrant-global:6333"
URL_DA_CONEXAO = "https://qdrant.exemplo.com"


class _RespostaDoQdrant(Exception):
    """Causa com ``status_code``, como a resposta HTTP do SDK do Qdrant."""

    def __init__(self, status_code: int | None) -> None:
        super().__init__(f"resposta {status_code}")
        self.status_code = status_code


class DestinoFalso:
    """Substitui ``build_vector_store``: guarda pontos por (url, coleção, escopo)."""

    def __init__(self) -> None:
        self.pontos: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.configuracoes: list[dict[str, Any]] = []
        self.falha_na_leitura: Exception | None = None

    def semear(self, url: str, colecao: str, escopo: str, ids: set[str]) -> None:
        self.pontos[(url, colecao)][escopo] |= ids

    def ids(self, url: str, colecao: str, escopo: str) -> set[str]:
        return set(self.pontos[(url, colecao)][escopo])

    def instalar(self, monkeypatch) -> None:
        destino = self

        class _Adaptador:
            def __init__(self, configuracao: dict[str, Any]) -> None:
                destino.configuracoes.append(dict(configuracao))
                self._chave = (
                    configuracao.get("url", URL_GLOBAL),
                    configuracao.get("collection_name"),
                )

            def list_ids(self, scope) -> set[str]:
                if destino.falha_na_leitura is not None:
                    raise destino.falha_na_leitura
                return set(destino.pontos[self._chave][scope.project_id])

            def delete_ids(self, scope, ids) -> None:
                destino.pontos[self._chave][scope.project_id] -= set(ids)

        monkeypatch.setattr(
            "src.pipeline.indexing.build_vector_store",
            lambda configuracao, *a, **k: _Adaptador(configuracao),
        )

    def colecoes_alcancadas(self) -> set[str | None]:
        return {configuracao.get("collection_name") for configuracao in self.configuracoes}


def _erro_de_leitura(status_code: int | None) -> Exception:
    from src.pipeline.providers.errors import UnreliableScopeReadError

    erro = UnreliableScopeReadError(
        "A releitura paginada do escopo no Qdrant falhou; sincronização bloqueada."
    )
    erro.__cause__ = _RespostaDoQdrant(status_code)
    return erro


def _escopo(base_id: str) -> str:
    from src.app.tasks import scope_project_id

    return scope_project_id("tenant-1", "projeto-1", base_id)


def _criar_base(
    colecao: str, *, embeddings_id: str | None = None, qdrant_id: str | None = None
) -> str:
    from src.app.models import Base, Execution, Workspace

    with sessao_do_banco() as sessao:
        workspace = Workspace(tenant_id="tenant-1", project_id="projeto-1", nome="WS exclusão")
        sessao.add(workspace)
        sessao.flush()
        base = Base(
            tenant_id="tenant-1",
            project_id="projeto-1",
            workspace_id=workspace.id,
            nome="base-exclusao.md",
            origem="upload",
            collection_name=colecao,
            documentos=1,
            conexao_embeddings_id=embeddings_id,
            conexao_vector_store_id=qdrant_id,
        )
        sessao.add(base)
        sessao.flush()
        sessao.add(
            Execution(
                base_id=base.id,
                situacao="succeeded",
                etapa="concluido",
                previstos=1,
                inseridos=1,
                mantidos=0,
                removidos=0,
            )
        )
        sessao.commit()
        return base.id


def _base_com_conexoes(client: TestClient, colecao: str, **alteracoes: Any) -> tuple[str, dict]:
    embeddings = criar_conexao_ok(client, payload_embeddings())
    qdrant = criar_conexao_ok(client, payload_qdrant(**alteracoes))
    return _criar_base(colecao, embeddings_id=embeddings["id"], qdrant_id=qdrant["id"]), qdrant


def _preparar(tmp_path, monkeypatch) -> DestinoFalso:
    storage_temporario(tmp_path, monkeypatch)
    destino = DestinoFalso()
    destino.instalar(monkeypatch)
    return destino


def _apagar(client: TestClient, base_id: str):
    return client.delete(f"/api/v1/bases/{base_id}", headers=OWNER)


def _base_ativa(base_id: str) -> bool:
    from src.app.models import Base

    with sessao_do_banco() as sessao:
        base = sessao.get(Base, base_id)
        return base is not None and base.apagada_em is None


def test_apagar_base_usa_colecao_da_base(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0028 US-001 FR-001 NFR-002 AC-001"""
    destino = _preparar(tmp_path, monkeypatch)
    client = cliente()
    base_id = _criar_base("vivo test")
    destino.semear(URL_GLOBAL, "vivo test", _escopo(base_id), {"c1", "c2", "c3"})

    resposta = _apagar(client, base_id)

    assert resposta.status_code == 204, resposta.text
    assert "vivo test" in destino.colecoes_alcancadas()
    assert destino.ids(URL_GLOBAL, "vivo test", _escopo(base_id)) == set()
    assert not _base_ativa(base_id)


def test_apagar_base_nao_toca_colecao_padrao_nem_outras_bases(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0028 US-001 FR-001 NFR-002 AC-002"""
    destino = _preparar(tmp_path, monkeypatch)
    client = cliente()
    primeira = _criar_base("vivo test")
    segunda = _criar_base("vivo test")
    destino.semear(URL_GLOBAL, "vivo test", _escopo(primeira), {"a1"})
    destino.semear(URL_GLOBAL, "vivo test", _escopo(segunda), {"b1", "b2"})
    destino.semear(URL_GLOBAL, PADRAO, "outra-base", {"p1"})

    resposta = _apagar(client, primeira)

    assert resposta.status_code == 204, resposta.text
    assert PADRAO not in destino.colecoes_alcancadas()
    assert destino.ids(URL_GLOBAL, "vivo test", _escopo(primeira)) == set()
    assert destino.ids(URL_GLOBAL, "vivo test", _escopo(segunda)) == {"b1", "b2"}
    assert destino.ids(URL_GLOBAL, PADRAO, "outra-base") == {"p1"}


def test_apagar_base_sem_conexoes_usa_qdrant_global_com_colecao_da_base(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0028 US-001 FR-001 NFR-002 AC-003"""
    from src.app.settings import get_settings

    destino = _preparar(tmp_path, monkeypatch)
    client = cliente()
    base_id = _criar_base("colecao-legada")
    destino.semear(URL_GLOBAL, "colecao-legada", _escopo(base_id), {"l1"})

    resposta = _apagar(client, base_id)

    assert resposta.status_code == 204, resposta.text
    alcancadas = [c for c in destino.configuracoes if c.get("collection_name") == "colecao-legada"]
    assert alcancadas, f"a coleção da Base não foi usada: {destino.configuracoes}"
    assert alcancadas[0].get("provider") == get_settings().vector_store.get("provider")
    assert destino.ids(URL_GLOBAL, "colecao-legada", _escopo(base_id)) == set()


def test_apagar_base_com_conexoes_usa_qdrant_da_conexao(tmp_path, monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0028 US-002 FR-002 FR-005 NFR-001 AC-004"""
    destino = _preparar(tmp_path, monkeypatch)
    client = cliente()
    base_id, qdrant = _base_com_conexoes(client, "vivo test")
    destino.semear(URL_DA_CONEXAO, "vivo test", _escopo(base_id), {"c1", "c2"})

    with caplog.at_level(logging.INFO):
        resposta = _apagar(client, base_id)

    assert resposta.status_code == 204, resposta.text
    usadas = [c for c in destino.configuracoes if c.get("url") == URL_DA_CONEXAO]
    assert usadas, f"o Qdrant da conexão não foi usado: {destino.configuracoes}"
    assert usadas[0]["collection_name"] == "vivo test"
    assert usadas[0].get("api_key") == CHAVE_QDRANT
    assert destino.ids(URL_DA_CONEXAO, "vivo test", _escopo(base_id)) == set()
    assert "vivo test" in caplog.text and qdrant["nome"] in caplog.text
    assert CHAVE_QDRANT not in caplog.text


def test_apagar_base_nao_vaza_chave_da_conexao(tmp_path, monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0028 US-002 FR-002 FR-005 NFR-001 AC-005"""
    destino = _preparar(tmp_path, monkeypatch)
    client = TestClient(cliente().app, raise_server_exceptions=False)
    base_id, _qdrant = _base_com_conexoes(client, "vivo test")
    destino.semear(URL_DA_CONEXAO, "vivo test", _escopo(base_id), {"c1"})

    with caplog.at_level(logging.DEBUG):
        sucesso = _apagar(client, base_id)
        assert sucesso.status_code == 204, sucesso.text

        outra_id, _ = _base_com_conexoes(client, "outra colecao")
        destino.falha_na_leitura = _erro_de_leitura(500)
        falha = _apagar(client, outra_id)

    assert falha.status_code >= 500
    for texto in (sucesso.text, falha.text, caplog.text):
        assert CHAVE_QDRANT not in texto
    assert any(c.get("url") == URL_DA_CONEXAO for c in destino.configuracoes)


def test_apagar_base_com_conexao_desativada_bloqueia_sem_alterar_postgres(
    tmp_path, monkeypatch
) -> None:
    """SPECSFY: SPEC-0028 US-002 FR-002 FR-004 NFR-001 AC-006"""
    from src.app.models import Conexao

    destino = _preparar(tmp_path, monkeypatch)
    client = cliente()
    base_id, qdrant = _base_com_conexoes(client, "vivo test")
    destino.semear(URL_DA_CONEXAO, "vivo test", _escopo(base_id), {"c1"})
    with sessao_do_banco() as sessao:
        sessao.get(Conexao, qdrant["id"]).situacao = "desativada"
        sessao.commit()

    resposta = _apagar(client, base_id)

    assert resposta.status_code == 409, resposta.text
    assert "reativ" in resposta.json()["detail"].lower()
    assert CHAVE_QDRANT not in resposta.text
    assert _base_ativa(base_id)
    assert destino.ids(URL_DA_CONEXAO, "vivo test", _escopo(base_id)) == {"c1"}


def test_apagar_base_com_colecao_ausente_conclui(tmp_path, monkeypatch, caplog) -> None:
    """SPECSFY: SPEC-0028 US-003 FR-003 FR-005 AC-007"""
    destino = _preparar(tmp_path, monkeypatch)
    client = TestClient(cliente().app, raise_server_exceptions=False)
    base_id = _criar_base("colecao-removida")
    destino.falha_na_leitura = _erro_de_leitura(404)

    with caplog.at_level(logging.INFO):
        resposta = _apagar(client, base_id)

    assert resposta.status_code == 204, resposta.text
    assert "colecao-removida" in destino.colecoes_alcancadas()
    assert not _base_ativa(base_id)
    assert "colecao-removida" in caplog.text
    assert "ausente" in caplog.text.lower()


def test_apagar_base_com_qdrant_indisponivel_bloqueia(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0028 US-003 FR-003 FR-004 NFR-002 AC-008"""
    destino = _preparar(tmp_path, monkeypatch)
    client = TestClient(cliente().app, raise_server_exceptions=False)
    base_id = _criar_base("vivo test")
    destino.semear(URL_GLOBAL, "vivo test", _escopo(base_id), {"c1"})

    for causa in (500, None):
        destino.falha_na_leitura = _erro_de_leitura(causa)
        resposta = _apagar(client, base_id)

        assert resposta.status_code >= 500, (causa, resposta.text)
        assert "vivo test" in destino.colecoes_alcancadas()
        assert _base_ativa(base_id), f"a Base foi apagada diante da falha {causa}"
        assert destino.ids(URL_GLOBAL, "vivo test", _escopo(base_id)) == {"c1"}


def test_apagar_base_repete_apos_falha_do_qdrant_conclui(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0028 US-003 FR-003 FR-004 NFR-002 AC-009"""
    destino = _preparar(tmp_path, monkeypatch)
    client = TestClient(cliente().app, raise_server_exceptions=False)
    base_id = _criar_base("vivo test")
    destino.semear(URL_GLOBAL, "vivo test", _escopo(base_id), {"c1", "c2"})
    destino.falha_na_leitura = _erro_de_leitura(500)

    primeira = _apagar(client, base_id)
    assert primeira.status_code >= 500
    assert _base_ativa(base_id)

    destino.falha_na_leitura = None
    segunda = _apagar(client, base_id)

    assert segunda.status_code == 204, segunda.text
    assert "vivo test" in destino.colecoes_alcancadas()
    assert destino.ids(URL_GLOBAL, "vivo test", _escopo(base_id)) == set()
    assert not _base_ativa(base_id)
