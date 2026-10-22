"""Regras fixas de limpeza: ruído óbvio sem IA (SPEC-0037, FR-001, FR-002).

Remove somente linhas inteiras. Número dentro de frase, linha curta de negócio e
qualquer texto fora dos padrões abaixo permanecem intactos.
"""

from __future__ import annotations

import re
from collections import Counter

from src.pipeline.limpeza.contratos import Exclusao, ResultadoLimpeza

MINIMO_REPETICOES = 3
TAMANHO_MAXIMO_RODAPE = 120
TAMANHO_MINIMO_RODAPE = 8

_NUMERO_PAGINA = re.compile(
    r"^(?:-\s*)?(?:(?:p[áa]gina|p[áa]g\.?|page)\s+)?\d{1,4}"
    r"(?:\s*(?:de|/|of)\s*\d{1,4})?(?:\s*-)?$",
    re.IGNORECASE,
)
_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
_SEPARADORES = re.compile(r"[\s|·•\-–—/>»]+")
_COOKIES = re.compile(
    r"(?:\b(?:utilizamos|usamos|este\s+site\s+(?:usa|utiliza)|nosso\s+site\s+(?:usa|utiliza))\b"
    r".{0,80}\bcookies\b|\baceitar\s+(?:todos\s+os\s+)?cookies\b)",
    re.IGNORECASE,
)
_SAUDACAO = re.compile(
    r"^(?:prezad[oa]s?|ol[áa]|bom\s+dia|boa\s+tarde|boa\s+noite|atenciosamente|abra[çc]os?|"
    r"cordialmente|obrigad[oa]s?|at\.te)[\s,.!:]*$",
    re.IGNORECASE,
)
_ITENS_MENU = frozenset({"menu", "pular para o conteúdo", "skip to content", "voltar ao topo"})


def _motivo(linha: str) -> str | None:
    if _NUMERO_PAGINA.match(linha):
        return "Número de página"
    if _SAUDACAO.match(linha):
        return "Saudação social"
    if linha.casefold() in _ITENS_MENU:
        return "Item de menu"
    links = _LINK.findall(linha)
    if len(links) >= 3 and not _SEPARADORES.sub("", _LINK.sub("", linha)):
        return "Item de menu"
    if len(linha) <= 200 and _COOKIES.search(linha):
        return "Aviso de cookies"
    return None


def aplicar_regras_fixas(markdown: str, arquivo: str) -> ResultadoLimpeza:
    linhas = markdown.split("\n")
    candidatas = Counter(
        linha.strip()
        for linha in linhas
        if TAMANHO_MINIMO_RODAPE <= len(linha.strip()) <= TAMANHO_MAXIMO_RODAPE
        and not linha.lstrip().startswith(("#", "|", "-", "*", ">", "```"))
    )
    repetidas = {t for t, n in candidatas.items() if n >= MINIMO_REPETICOES}
    mantidas: list[str] = []
    exclusoes: list[Exclusao] = []
    for numero, linha in enumerate(linhas, start=1):
        limpa = linha.strip()
        motivo = None
        if limpa:
            motivo = _motivo(limpa)
            if motivo is None and limpa in repetidas:
                motivo = "Linha repetida (rodapé ou cabeçalho)"
        if motivo:
            exclusoes.append(Exclusao(arquivo, numero, motivo, "regra", limpa))
        else:
            mantidas.append(linha)
    if not exclusoes:
        return ResultadoLimpeza(markdown, [])
    texto = re.sub(r"\n{3,}", "\n\n", "\n".join(mantidas))
    return ResultadoLimpeza(texto, exclusoes)
