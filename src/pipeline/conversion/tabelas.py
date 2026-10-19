"""Tabelas simples, complexas e contínuas entre páginas (SPEC-0040, FR-005 e FR-006).

Tabela simples (colunas consistentes, cabeçalho de um nível, sem células mescladas) sai como
tabela Markdown. Tabela complexa vira texto corrido, uma frase por linha, com o aviso
``tabela_complexa_virou_texto``. A tabela que termina uma página e continua no início da seguinte
é juntada quando o número de colunas bate (sem repetir o cabeçalho); em dúvida, não junta e avisa
com ``tabela_nao_juntada``. Nada é juntado ou simplificado em silêncio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.pipeline.conversion.contracts import AvisoConversao

MSG_COMPLEXA = "tabela complexa virou texto"
MSG_NAO_JUNTADA = "tabela não juntada"
_SEPARADOR = re.compile(r"^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


@dataclass(frozen=True)
class Texto:
    conteudo: str


@dataclass(frozen=True)
class Tabela:
    linhas: list[list[str]]
    cabecalho_niveis: int = 1
    mesclada: bool = False
    original: str | None = None  # Markdown original, preservado quando nada muda


@dataclass(frozen=True)
class ResultadoTabelas:
    markdown: str
    avisos: list[AvisoConversao] = field(default_factory=list)


@dataclass
class _Item:
    pagina: int
    texto: str | None = None
    linhas: list[list[str]] | None = None
    niveis: int = 1
    mesclada: bool = False
    original: str | None = None
    modificada: bool = False
    removida: bool = False

    @property
    def tabela(self) -> bool:
        return self.linhas is not None

    @property
    def complexa(self) -> bool:
        if not self.linhas:
            return False
        colunas = len(self.linhas[0])
        return (
            self.mesclada or self.niveis > 1 or any(len(linha) != colunas for linha in self.linhas)
        )


def _celula(valor: str) -> str:
    return " ".join(valor.replace("|", "\\|").split())


def _linha(celulas: list[str]) -> str:
    return "| " + " | ".join(_celula(c) for c in celulas) + " |"


def _como_markdown(item: _Item) -> str:
    assert item.linhas is not None
    cabecalho, *dados = item.linhas
    linhas = [_linha(cabecalho), _linha(["---"] * len(cabecalho)), *map(_linha, dados)]
    return "\n".join(linhas)


def _como_texto(item: _Item) -> str:
    assert item.linhas is not None
    niveis = max(1, item.niveis)
    cabecalho, dados = item.linhas[:niveis], item.linhas[niveis:]
    colunas = max(len(linha) for linha in item.linhas)
    rotulos = [
        " ".join(c for linha in cabecalho if i < len(linha) and (c := linha[i].strip()))
        for i in range(colunas)
    ]
    saida = [
        "Colunas: " + "; ".join(c.strip() for c in linha if c.strip()) + "."
        for linha in cabecalho
        if any(c.strip() for c in linha)
    ]
    for linha in dados:
        partes = [
            f"{rotulos[i]}: {valor.strip()}" if i < len(rotulos) and rotulos[i] else valor.strip()
            for i, valor in enumerate(linha)
            if valor.strip()
        ]
        if partes:
            saida.append("; ".join(partes) + ".")
    return "\n".join(saida)


def _juntar(paginas: list[list[_Item]]) -> list[AvisoConversao]:
    avisos: list[AvisoConversao] = []
    candidata: _Item | None = None
    for blocos in paginas:
        if not blocos:
            candidata = None
            continue
        primeiro = blocos[0]
        if candidata is not None and primeiro.tabela:
            anterior = candidata
            if anterior.complexa or primeiro.complexa:
                pass
            elif len(anterior.linhas[0]) != len(primeiro.linhas[0]):  # type: ignore[index]
                avisos.append(
                    AvisoConversao("tabela_nao_juntada", primeiro.pagina + 1, MSG_NAO_JUNTADA)
                )
            else:
                novas = primeiro.linhas[:]  # type: ignore[index]
                repetido = [c.strip() for c in novas[0]] == [
                    c.strip()
                    for c in anterior.linhas[0]  # type: ignore[index]
                ]
                anterior.linhas.extend(novas[1:] if repetido else novas)  # type: ignore[union-attr]
                anterior.modificada = True
                primeiro.removida = True
                if len(blocos) == 1:
                    anterior.pagina = primeiro.pagina
                    continue  # a tabela continua para a página seguinte
        ultimo = blocos[-1]
        candidata = ultimo if ultimo.tabela and not ultimo.removida else None
    return avisos


def _avisos_de_complexas(paginas: list[list[_Item]]) -> list[AvisoConversao]:
    return [
        AvisoConversao("tabela_complexa_virou_texto", item.pagina + 1, MSG_COMPLEXA)
        for blocos in paginas
        for item in blocos
        if item.tabela and not item.removida and item.complexa
    ]


def _renderizar(item: _Item) -> str:
    if not item.tabela:
        return item.texto or ""
    if item.complexa:
        return _como_texto(item)
    if item.original is not None and not item.modificada:
        return item.original
    return _como_markdown(item)


def _itens(paginas) -> list[list[_Item]]:
    saida = []
    for indice, blocos in enumerate(paginas):
        itens = []
        for bloco in blocos:
            if isinstance(bloco, Tabela):
                itens.append(
                    _Item(
                        indice,
                        linhas=[list(linha) for linha in bloco.linhas],
                        niveis=bloco.cabecalho_niveis,
                        mesclada=bloco.mesclada,
                        original=bloco.original,
                    )
                )
            else:
                itens.append(_Item(indice, texto=bloco.conteudo))
        saida.append(itens)
    return saida


def normalizar_tabelas(paginas: list[list[Texto | Tabela]]) -> ResultadoTabelas:
    """Normaliza as tabelas de um documento dividido em páginas (listas de blocos)."""
    itens = _itens(paginas)
    avisos = _juntar(itens)
    avisos += _avisos_de_complexas(itens)
    partes = [_renderizar(i) for pagina in itens for i in pagina if not i.removida]
    return ResultadoTabelas("\n\n".join(p for p in partes if p), avisos)


def _celulas(linha: str) -> list[str]:
    corpo = linha.strip().strip("|")
    return [c.strip() for c in corpo.split("|")]


def blocos_de_markdown(markdown: str) -> list[Texto | Tabela]:
    """Divide o Markdown de uma página em texto e tabelas, preservando o texto original."""
    linhas = markdown.splitlines(keepends=True)
    blocos: list[Texto | Tabela] = []
    texto: list[str] = []
    i = 0
    while i < len(linhas):
        if (
            linhas[i].lstrip().startswith("|")
            and i + 1 < len(linhas)
            and _SEPARADOR.match(linhas[i + 1].strip())
        ):
            fim = i + 2
            while fim < len(linhas) and linhas[fim].lstrip().startswith("|"):
                fim += 1
            if texto:
                blocos.append(Texto("".join(texto)))
                texto = []
            trecho = linhas[i:fim]
            celulas = [_celulas(linha) for k, linha in enumerate(trecho) if k != 1]
            cabecalho = celulas[0]
            multi = any(not c for c in cabecalho) and any(cabecalho)
            blocos.append(
                Tabela(celulas, cabecalho_niveis=2 if multi else 1, original="".join(trecho))
            )
            i = fim
        else:
            texto.append(linhas[i])
            i += 1
    if texto:
        blocos.append(Texto("".join(texto)))
    return blocos


def normalizar_paginas_markdown(paginas: list[str]) -> ResultadoTabelas:
    """Pós-processa o Markdown de cada página de um PDF; sem tabelas, o texto não muda."""
    divididas = [blocos_de_markdown(p) for p in paginas]
    if not any(isinstance(b, Tabela) for pagina in divididas for b in pagina):
        return ResultadoTabelas("".join(paginas), [])
    itens = _itens(divididas)
    avisos = _juntar(itens)
    avisos += _avisos_de_complexas(itens)
    saida = []
    for pagina in itens:
        for item in pagina:
            if item.removida:
                continue
            texto = _renderizar(item)
            saida.append(texto if not item.tabela or item.original == texto else texto + "\n\n")
    return ResultadoTabelas("".join(saida), avisos)
