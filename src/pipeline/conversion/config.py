"""Configuração não sensível do OCR, injetada nos conversores (SPEC-0033)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class ConversaoConfig:
    idioma: str = "por+eng"
    limite_paginas_ocr: int = 50
    minimo_texto_util: int = 40

    max_arquivos: int = 50
    max_bytes_arquivo: int = 40 * 1024 * 1024
    max_bytes_lote: int = 50 * 1024 * 1024
    timeout_url_s: float = 10
    max_bytes_url: int = 5 * 1024 * 1024
    max_redirecionamentos: int = 5
    max_proporcao_substituicao: float = 0.05

    def __post_init__(self) -> None:
        if not isinstance(self.idioma, str) or not self.idioma.strip():
            raise ValueError("conversao.idioma deve ser um texto não vazio.")
        for campo in (
            "limite_paginas_ocr",
            "minimo_texto_util",
            "max_arquivos",
            "max_bytes_arquivo",
            "max_bytes_lote",
            "max_bytes_url",
        ):
            valor = getattr(self, campo)
            if type(valor) is not int or valor <= 0:
                raise ValueError(f"conversao.{campo} deve ser um inteiro positivo.")

        if type(self.max_redirecionamentos) is not int or self.max_redirecionamentos < 0:
            raise ValueError("conversao.max_redirecionamentos deve ser não negativo.")
        import math

        if (
            type(self.timeout_url_s) not in (int, float)
            or not math.isfinite(self.timeout_url_s)
            or self.timeout_url_s <= 0
        ):
            raise ValueError("conversao.timeout_url_s deve ser positivo e finito.")
        if (
            type(self.max_proporcao_substituicao) not in (int, float)
            or not 0 <= self.max_proporcao_substituicao <= 1
        ):
            raise ValueError("conversao.max_proporcao_substituicao deve estar entre 0 e 1.")


def carregar_config_conversao(config: Mapping) -> ConversaoConfig:
    secao = config.get("conversao", {})
    if not isinstance(secao, Mapping):
        raise ValueError("conversao deve ser um objeto.")  # noqa: TRY004 — erro de configuração
    padrao = ConversaoConfig()
    return ConversaoConfig(
        **{
            campo.name: secao.get(campo.name, getattr(padrao, campo.name))
            for campo in fields(ConversaoConfig)
        }
    )
