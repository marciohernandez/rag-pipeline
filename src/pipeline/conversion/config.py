"""Configuração não sensível do OCR, injetada nos conversores (SPEC-0033)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ConversaoConfig:
    idioma: str = "por+eng"
    limite_paginas_ocr: int = 50
    minimo_texto_util: int = 40

    def __post_init__(self) -> None:
        if not isinstance(self.idioma, str) or not self.idioma.strip():
            raise ValueError("conversao.idioma deve ser um texto não vazio.")
        for campo in ("limite_paginas_ocr", "minimo_texto_util"):
            valor = getattr(self, campo)
            if type(valor) is not int or valor <= 0:
                raise ValueError(f"conversao.{campo} deve ser um inteiro positivo.")


def carregar_config_conversao(config: Mapping) -> ConversaoConfig:
    secao = config.get("conversao", {})
    if not isinstance(secao, Mapping):
        raise ValueError("conversao deve ser um objeto.")  # noqa: TRY004 — erro de configuração
    padrao = ConversaoConfig()
    return ConversaoConfig(
        **{
            campo: secao.get(campo, getattr(padrao, campo))
            for campo in ("idioma", "limite_paginas_ocr", "minimo_texto_util")
        }
    )
