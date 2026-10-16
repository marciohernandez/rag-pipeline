"""Relatório Markdown da limpeza de um lote, sem o texto removido (SPEC-0037, FR-007)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from src.pipeline.limpeza.contratos import Exclusao, ParDuplicado


@dataclass
class DocumentoRelatorio:
    arquivo: str
    exclusoes: Sequence[Exclusao] = field(default_factory=list)
    duvidas: Sequence[str] = field(default_factory=list)
    revisar: Sequence[str] = field(default_factory=list)
    falha: str | None = None


def montar_relatorio(
    documentos: Sequence[DocumentoRelatorio],
    provaveis: Sequence[ParDuplicado],
    *,
    ia_usada: bool,
    provedor: str | None,
    dominio_versao: int | None,
    motivo_sem_ia: str | None = None,
) -> str:
    linhas = ["# Relatório do lote", ""]
    linhas.append(f"Versão do domínio: {dominio_versao if dominio_versao is not None else '—'}")
    if ia_usada:
        linhas.append(f"Análise por IA: sim ({provedor or 'provedor não informado'})")
    else:
        linhas.append(
            f"Análise por IA: não — etapa de IA não rodou ({motivo_sem_ia or 'desligada'})"
        )
    linhas += ["", "## Exclusões"]
    if not any(d.exclusoes for d in documentos):
        linhas.append("Nenhuma exclusão.")
    for doc in documentos:
        for e in doc.exclusoes:
            origem = f" (mantido em {e.mantido_em})" if e.mantido_em else ""
            conf = f", confiança {e.confianca:.2f}" if e.confianca is not None else ""
            linhas.append(
                f"- {e.arquivo}, posição {e.posicao}: {e.motivo} [{e.camada}{conf}]{origem}"
            )
    linhas += ["", "## Dúvidas"]
    if not any(d.duvidas for d in documentos):
        linhas.append("Nenhuma dúvida.")
    for doc in documentos:
        for trecho in doc.duvidas:
            linhas.append(f"- {doc.arquivo}: {' '.join(trecho.split())[:300]}")
    linhas += ["", "## Duplicidades prováveis"]
    if not provaveis:
        linhas.append("Nenhuma.")
    for par in provaveis:
        linhas.append(f"- {par.arquivo_a} e {par.arquivo_b} ({par.semelhanca:.0%} de semelhança)")
    revisar = [(d.arquivo, motivo) for d in documentos for motivo in d.revisar]
    if revisar:
        linhas += ["", "## Revisar"]
        linhas += [f"- {arquivo}: {motivo}" for arquivo, motivo in revisar]
    falhas = [d for d in documentos if d.falha]
    if falhas:
        linhas += ["", "## Falhas"]
        linhas += [f"- {d.arquivo}: {d.falha}" for d in falhas]
    return "\n".join(linhas) + "\n"
