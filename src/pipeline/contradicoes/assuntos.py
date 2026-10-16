"""Normalização e agrupamento de afirmações por assunto (SPEC-0038, FR-002)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from src.pipeline.contradicoes.contratos import Afirmacao, Julgamento

MAXIMO_POR_JULGAMENTO = 20
_LIGACAO = frozenset(
    {"de", "do", "da", "dos", "das", "e", "o", "a", "os", "as", "em", "no", "na", "para", "por"}
)


def normalizar_assunto(texto: str) -> str:
    """Caixa, acentos, pontuação, palavras de ligação e ordem das palavras não importam."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    palavras = re.findall(r"[a-z0-9]+", sem_acento.lower())
    return " ".join(sorted(p for p in palavras if p not in _LIGACAO))


def agrupar(afirmacoes: Sequence[Afirmacao]) -> dict[str, list[Afirmacao]]:
    grupos: dict[str, list[Afirmacao]] = {}
    for afirmacao in afirmacoes:
        chave = normalizar_assunto(afirmacao.assunto)
        if chave:
            grupos.setdefault(chave, []).append(afirmacao)
    return grupos


def planejar_julgamentos(
    afirmacoes: Sequence[Afirmacao], maximo_por_julgamento: int = MAXIMO_POR_JULGAMENTO
) -> list[Julgamento]:
    """Um julgamento por assunto; assunto com uma só afirmação não é julgado."""
    julgamentos: list[Julgamento] = []
    for assunto, grupo in agrupar(afirmacoes).items():
        if len(grupo) < 2:
            continue
        for inicio in range(0, len(grupo), maximo_por_julgamento):
            parte = grupo[inicio : inicio + maximo_por_julgamento]
            if len(parte) >= 2:
                julgamentos.append(Julgamento(assunto, parte))
    return julgamentos
