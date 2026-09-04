"""Trava local contra um falso positivo do validador do Specsfy.

`validate_spec.mjs` reprova uma spec com a mensagem genérica
`Marcadores não resolvidos.` quando encontra
`/\\b(?:TODO|TBD|FIXME)\\b|\\[NEEDS CLARIFICATION/im` no corpo do arquivo.

O flag `i` faz `TODO` casar também com a palavra portuguesa **todo**, comum em
texto técnico escrito em Português do Brasil — idioma que o próprio framework
exige em `.specsfy/Spec.md`. `toda`, `todos` e `todas` passam, porque o `\\b`
não fecha depois do `o`; apenas `todo` e `Todo` reprovam.

Este teste antecipa a reprovação com um diagnóstico útil, apontando arquivo,
linha e trecho. Ele não corrige a causa: a correção pertence ao repositório
`promovaweb/specsfy` e consiste em remover o flag `i`, já que marcador de
código é escrito em caixa alta por convenção.

Remova este arquivo quando o upstream corrigir o regex.
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Mesmo padrão aplicado por .agents/skills/specsfy-04-validate/scripts/validate_spec.mjs.
# re.ASCII é obrigatório para reproduzir o \b do JavaScript, que ignora acentos.
PADRAO_DO_VALIDADOR = re.compile(
    r"\b(?:TODO|TBD|FIXME)\b|\[NEEDS CLARIFICATION", re.IGNORECASE | re.ASCII
)

# A caixa separa os dois casos: marcador de código é escrito em caixa alta por
# convenção, então "TODO" é pendência real e "todo"/"Todo" é a palavra portuguesa.
# A comparação aqui é sensível à caixa de propósito.
PALAVRA_PORTUGUESA = re.compile(r"^(?:todo|Todo)$")


def _specs() -> list[Path]:
    """Somente `spec.md`: é o que o validador lê.

    `specs/inbox/` fica de fora de propósito, porque preserva a formulação
    original da pessoa e não pode ser reescrita para agradar um regex.
    """
    return sorted(RAIZ.glob("specs/*/*/spec.md"))


def _ocorrencias(caminho: Path) -> list[tuple[int, str, str]]:
    achados = []
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        for encontrado in PADRAO_DO_VALIDADOR.finditer(linha):
            achados.append((numero, encontrado.group(0), linha.strip()))
    return achados


def test_nenhuma_spec_dispara_o_falso_positivo_do_validador() -> None:
    relatorio: list[str] = []
    for caminho in _specs():
        for numero, trecho, linha in _ocorrencias(caminho):
            relativo = caminho.relative_to(RAIZ)
            if PALAVRA_PORTUGUESA.match(trecho):
                fuga = re.escape(trecho)
                dentro_de_palavra = re.search(rf"\w{fuga}|{fuga}\w", linha)
                causa = (
                    f'"{trecho}" dentro de outra palavra, como "método" — o \\b do '
                    "JavaScript fecha no acento; reescreva o termo ou remova o acento"
                    if dentro_de_palavra
                    else (
                        f'palavra portuguesa "{trecho}" — reescreva com "cada", '
                        '"qualquer", "inteiro" ou "na íntegra"'
                    )
                )
            else:
                causa = f'marcador "{trecho}" — resolva o pendente antes de aprovar o gate'
            relatorio.append(f"{relativo}:{numero}: {causa}\n    {linha}")

    assert not relatorio, (
        "Estas ocorrências fariam validate_spec.mjs reprovar com "
        '"Marcadores não resolvidos.":\n\n' + "\n".join(relatorio)
    )
