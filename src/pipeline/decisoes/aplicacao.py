"""Aplicação da correção: troca só o trecho alvo e preserva o resto do Markdown (SPEC-0039)."""

from __future__ import annotations

from src.pipeline.decisoes.localizacao import localizar_trecho


def aplicar_correcao(markdown: str, trecho_alvo: str, texto_corrigido: str) -> str:
    local = localizar_trecho(markdown, trecho_alvo)
    if local is None:
        raise ValueError("Trecho alvo não localizado no documento.")
    return markdown[: local.inicio] + texto_corrigido + markdown[local.fim :]
