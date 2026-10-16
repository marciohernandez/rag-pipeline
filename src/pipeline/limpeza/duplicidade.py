"""Duplicidade entre documentos do lote (SPEC-0037, FR-006).

Mantém uma cópia (a do primeiro documento na ordem do lote). Remove sozinha só a
igualdade após normalização ou a semelhança alta em trechos longos; o que fica
abaixo do limite, mas ainda parecido, vai à lista de duplicidades prováveis.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from difflib import SequenceMatcher

from src.pipeline.limpeza.contratos import Exclusao, ParDuplicado, ResultadoDuplicidade

MINIMO_CARACTERES = 200
LIMIAR = 0.95
LIMIAR_PROVAVEL = 0.8


def normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", sem_acento.casefold())).strip()


def _semelhanca(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b, autojunk=False).ratio()


def _paragrafos(markdown: str) -> list[tuple[int, str]]:
    blocos: list[tuple[int, str]] = []
    linha = 1
    for bloco in markdown.split("\n\n"):
        blocos.append((linha, bloco))
        linha += bloco.count("\n") + 2
    return blocos


def deduplicar(
    documentos: Sequence[tuple[str, str]],
    minimo_caracteres: int = MINIMO_CARACTERES,
    limiar: float = LIMIAR,
    limiar_provavel: float = LIMIAR_PROVAVEL,
) -> ResultadoDuplicidade:
    mantidos: list[tuple[str, str, str]] = []  # (arquivo, texto original, normalizado)
    saida: dict[str, str] = {}
    exclusoes: list[Exclusao] = []
    provaveis: list[ParDuplicado] = []
    for arquivo, markdown in documentos:
        restantes: list[str] = []
        antes = len(exclusoes)
        for linha, bloco in _paragrafos(markdown):
            texto = bloco.strip()
            normal = normalizar(texto)
            if not normal or texto.startswith("#"):
                restantes.append(bloco)
                continue
            removido = False
            for origem, original, normal_origem in mantidos:
                if origem == arquivo:
                    continue
                igual = normal == normal_origem
                longo = len(texto) >= minimo_caracteres and len(original) >= minimo_caracteres
                razao = 1.0 if igual else (_semelhanca(normal, normal_origem) if longo else 0.0)
                if igual or (longo and razao >= limiar):
                    motivo = (
                        "Duplicidade exata" if igual else f"Duplicidade quase exata ({razao:.0%})"
                    )
                    exclusoes.append(
                        Exclusao(arquivo, linha, motivo, "duplicidade", texto, mantido_em=origem)
                    )
                    removido = True
                    break
                if longo and razao >= limiar_provavel:
                    provaveis.append(ParDuplicado(origem, arquivo, original, texto, razao))
            if not removido:
                restantes.append(bloco)
                mantidos.append((arquivo, texto, normal))
        saida[arquivo] = "\n\n".join(restantes) if len(exclusoes) > antes else markdown
    return ResultadoDuplicidade(saida, exclusoes, provaveis)
