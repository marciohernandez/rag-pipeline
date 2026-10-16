"""Localização determinística do trecho alvo no Markdown (SPEC-0039, DEC-002)."""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from src.pipeline.decisoes.contratos import Localizacao

MINIMO_CARACTERES = 20


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    base = "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()
    return " ".join(re.sub(r"[^\w\s]", " ", base).split())


def _candidatos(markdown: str) -> list[tuple[int, int]]:
    """Parágrafos e linhas não vazias, com a posição de cada um no texto."""
    posicoes: set[tuple[int, int]] = set()
    for padrao in (r"\S[^\n]*", r"(?:[^\n]+\n?)+"):
        for achado in re.finditer(padrao, markdown):
            texto = achado.group(0)
            inicio = achado.start()
            fim = inicio + len(texto.rstrip())
            if fim > inicio:
                posicoes.add((inicio, fim))
    return sorted(posicoes)


def localizar_trecho(markdown: str, trecho: str, limiar: float = 0.9) -> Localizacao | None:
    """Acha o trecho por correspondência exata e, na falta dela, por semelhança alta.

    Devolve ``None`` quando o trecho é curto demais, não existe ou é ambíguo (aparece mais
    de uma vez ou há mais de um candidato acima do limiar).
    """
    alvo = trecho.strip()
    if len(alvo) < MINIMO_CARACTERES:
        return None
    ocorrencias = markdown.count(alvo)
    if ocorrencias == 1:
        inicio = markdown.index(alvo)
        return Localizacao(inicio, inicio + len(alvo), True)
    if ocorrencias > 1:
        return None
    normalizado = _normalizar(alvo)
    if not normalizado:
        return None
    aprovados: list[tuple[float, int, int]] = []
    for inicio, fim in _candidatos(markdown):
        razao = SequenceMatcher(None, normalizado, _normalizar(markdown[inicio:fim])).ratio()
        if razao >= limiar:
            aprovados.append((razao, inicio, fim))
    if not aprovados:
        return None
    aprovados.sort(key=lambda a: (-a[0], a[2] - a[1]))
    _, inicio, fim = aprovados[0]
    if any(not (i < fim and inicio < f) for _, i, f in aprovados[1:]):
        return None  # outro candidato semelhante em outro ponto do documento: ambíguo
    return Localizacao(inicio, fim, False)
