"""Worker de envio com conexões (SPEC-0026 e SPEC-0030).

O job só leva o identificador do envio; o worker lê a coleção, decifra as chaves em
memória e revalida a URL da conexão antes de conectar.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace

from tests._colecoes import OWNER, enviar, md, preparar, texto_com_secoes
from tests._conexoes import CHAVE_EMBEDDINGS, CHAVE_QDRANT
from tests._pessoas import sessao_do_banco


def _executar(envio_id: str, monkeypatch, *, falhar: bool = False) -> dict:
    """Roda o worker com a fachada falsa e devolve a configuração que ele montou."""
    from src.app import tasks

    capturado: dict = {}

    def run_pipeline(config, **kwargs):
        capturado["config"] = config
        return SimpleNamespace(chunks=[])

    def sync(config, chunks, on_document=None):
        if falhar:
            raise RuntimeError("falha simulada do destino")
        return SimpleNamespace(previstos=0, inseridos=0, mantidos=0, removidos=0)

    monkeypatch.setattr("src.pipeline.service.run_pipeline", run_pipeline)
    monkeypatch.setattr("src.pipeline.service.sync_documents", sync)
    tasks.process_envio_task.func(envio_id)
    return capturado


def test_worker_decifra_so_em_memoria_e_a_repeticao_reusa_os_parametros(
    tmp_path, monkeypatch, caplog
) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013"""
    ambiente = preparar(tmp_path, monkeypatch)
    resposta = enviar(
        ambiente,
        [md("a.md", texto_com_secoes(2))],
        nova="politicas",
        executar=False,
        chunk_size=800,
        chunk_overlap=100,
    )
    assert resposta.status_code == 201, resposta.text
    envio_id = resposta.json()["envio_id"]

    assert ambiente.agendamentos == [{"envio_id": envio_id}]
    assert ambiente.locks == [f"colecao:{resposta.json()['colecao_id']}"]
    texto_dos_argumentos = json.dumps(ambiente.agendamentos, default=str)
    assert CHAVE_EMBEDDINGS not in texto_dos_argumentos
    assert CHAVE_QDRANT not in texto_dos_argumentos

    with caplog.at_level(logging.DEBUG):
        configuracao = _executar(envio_id, monkeypatch, falhar=True)["config"]
    assert configuracao["chunking"]["default_splitter"] == "header"
    assert configuracao["chunking"]["default_chunk_size"] == 800
    assert configuracao["chunking"]["default_chunk_overlap"] == 100
    assert "sync_mode" not in configuracao["vector_store"]
    assert CHAVE_EMBEDDINGS not in caplog.text and CHAVE_QDRANT not in caplog.text
    envio = ambiente.client.get(f"/api/v1/envios/{envio_id}", headers=OWNER)
    assert envio.json()["situacao"] == "failed"

    repeticao = ambiente.client.post(f"/api/v1/envios/{envio_id}/retry", headers=OWNER)
    assert repeticao.status_code == 202, repeticao.text
    assert ambiente.agendamentos[-1] == {"envio_id": envio_id}


def test_worker_revalida_a_url_da_conexao_antes_de_conectar(tmp_path, monkeypatch) -> None:
    """SPECSFY: SPEC-0026 US-003 FR-010 FR-011 NFR-001 NFR-005 AC-013"""
    ambiente = preparar(tmp_path, monkeypatch)
    resposta = enviar(ambiente, [md("a.md", texto_com_secoes(2))], nova="politicas", executar=False)
    envio_id = resposta.json()["envio_id"]
    from src.app.models import Conexao

    with sessao_do_banco() as sessao:
        sessao.get(Conexao, ambiente.qdrant_id).configuracao = {
            "url": "http://169.254.169.254/latest"
        }
        sessao.commit()

    configuracao = _executar(envio_id, monkeypatch)

    assert "config" not in configuracao
    envio = ambiente.client.get(f"/api/v1/envios/{envio_id}", headers=OWNER)
    assert envio.json()["situacao"] == "failed"
    assert "169.254" not in envio.text
