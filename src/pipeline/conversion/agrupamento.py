"""Proposta de grupos e ordem de imagens por metadados locais (SPEC-0040, FR-001).

Usa somente o nome do arquivo (prefixo e numeração), a data e hora e a pasta de origem: nunca lê
o conteúdo da imagem, não roda OCR e não faz chamada de rede (NFR-002 e NFR-003).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import PurePath

_NUMERADO = re.compile(r"^(?P<prefixo>.*?)[\s_\-.()]*(?P<numero>\d+)[\s_\-.()]*$")


@dataclass(frozen=True)
class ArquivoImagem:
    nome: str
    modificado_em: datetime | None = None
    pasta: str | None = None


@dataclass(frozen=True)
class GrupoProposto:
    arquivos: list[str]
    certeza: str


@dataclass(frozen=True)
class PropostaGrupos:
    grupos: list[GrupoProposto] = field(default_factory=list)
    certeza: str = "incerta"


@dataclass(frozen=True)
class _Pista:
    arquivo: ArquivoImagem
    prefixo: str | None
    numero: int | None


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold().strip()


def _pista(arquivo: ArquivoImagem) -> _Pista:
    radical = PurePath(arquivo.nome).stem
    achado = _NUMERADO.match(radical)
    if achado:
        return _Pista(arquivo, _normalizar(achado["prefixo"]), int(achado["numero"]))
    return _Pista(arquivo, None, None)


def _ordem(pista: _Pista):
    quando = pista.arquivo.modificado_em
    return (
        pista.numero is None,
        pista.numero or 0,
        quando is None,
        quando.timestamp() if quando else 0.0,
        pista.arquivo.nome,
    )


def _separar_por_tempo(pistas: list[_Pista], intervalo_max: timedelta) -> list[list[_Pista]]:
    pedacos: list[list[_Pista]] = []
    for pista in pistas:
        anterior = pedacos[-1][-1].arquivo.modificado_em if pedacos else None
        atual = pista.arquivo.modificado_em
        if pedacos and not (
            anterior is not None and atual is not None and abs(atual - anterior) > intervalo_max
        ):
            pedacos[-1].append(pista)
        else:
            pedacos.append([pista])
    return pedacos


def _certo(pistas: list[_Pista]) -> bool:
    """Nome numerado, data e pasta presentes e a numeração concorda com a ordem do tempo."""
    if len(pistas) < 2:
        return all(
            p.arquivo.modificado_em is not None and p.arquivo.pasta is not None for p in pistas
        )
    if any(
        p.numero is None or p.arquivo.modificado_em is None or p.arquivo.pasta is None
        for p in pistas
    ):
        return False
    numeros = [p.numero for p in pistas]
    tempos = [p.arquivo.modificado_em for p in pistas]
    return len(set(numeros)) == len(numeros) and tempos == sorted(tempos)


def propor_grupos(
    arquivos: list[ArquivoImagem], intervalo_max: timedelta = timedelta(minutes=10)
) -> PropostaGrupos:
    """Grupos e ordem sugerida; ``certeza`` é ``total`` só quando as três pistas concordam."""
    baldes: dict[tuple[str, str | None], list[_Pista]] = {}
    for arquivo in arquivos:
        pista = _pista(arquivo)
        chave = ((arquivo.pasta or ""), pista.prefixo)
        baldes.setdefault(chave, []).append(pista)
    grupos: list[list[_Pista]] = []
    for pistas in baldes.values():
        grupos.extend(_separar_por_tempo(sorted(pistas, key=_ordem), intervalo_max))

    def primeiro_instante(grupo: list[_Pista]):
        tempos = [p.arquivo.modificado_em for p in grupo if p.arquivo.modificado_em]
        return (not tempos, min(tempos).timestamp() if tempos else 0.0, grupo[0].arquivo.nome)

    grupos.sort(key=primeiro_instante)
    propostos = [
        GrupoProposto([p.arquivo.nome for p in grupo], "total" if _certo(grupo) else "incerta")
        for grupo in grupos
    ]
    total = bool(propostos) and all(g.certeza == "total" for g in propostos)
    return PropostaGrupos(propostos, "total" if total else "incerta")
