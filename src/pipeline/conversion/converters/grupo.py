"""Conversor de um grupo de imagens em um único Markdown (SPEC-0040, FR-003 e FR-004).

Cada imagem vira uma seção, na ordem recebida (a ordem aprovada pela pessoa), com a linha
``Origem: <arquivo>``. A imagem sem texto reconhecido vira ``imagem não legível: <arquivo>`` e o
documento recebe o aviso ``imagem_nao_legivel`` ("Revisar"). O corpo é texto livre, sem
frontmatter, compatível com a SPEC-0002.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from src.pipeline.conversion.config import ConversaoConfig
from src.pipeline.conversion.contracts import AvisoConversao, ConversionResult, DocumentConverter
from src.pipeline.conversion.converters.image import ImageConverter

_SEM_TEXTO = "ocr_sem_texto_reconhecido"


@dataclass
class GrupoImagensConverter:
    conversor_imagem: DocumentConverter | None = None
    config: ConversaoConfig = field(default_factory=ConversaoConfig)

    def converter(self, caminhos: Sequence[Path]) -> ConversionResult:
        conversor = self.conversor_imagem or ImageConverter(config=self.config)
        secoes: list[str] = []
        avisos: list[AvisoConversao] = []
        for posicao, caminho in enumerate(caminhos, 1):
            resultado = conversor.converter(Path(caminho))
            nome = Path(caminho).name
            ilegivel = any(a.codigo == _SEM_TEXTO for a in resultado.avisos) or not (
                resultado.markdown.strip()
            )
            avisos.extend(a for a in resultado.avisos if a.codigo != _SEM_TEXTO)
            if ilegivel:
                corpo = f"imagem não legível: {nome}"
                avisos.append(AvisoConversao("imagem_nao_legivel", None, corpo))
            else:
                corpo = resultado.markdown.strip()
            secoes.append(f"## Imagem {posicao}\n\nOrigem: {nome}\n\n{corpo}")
        return ConversionResult(markdown="\n\n".join(secoes) + "\n", avisos=avisos)
