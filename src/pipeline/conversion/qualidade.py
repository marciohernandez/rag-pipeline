"""Sinais determinísticos de qualidade; não chama provedores de IA."""

from src.pipeline.conversion.config import ConversaoConfig
from src.pipeline.conversion.contracts import AvisoConversao


def avaliar_qualidade(markdown: str, config: ConversaoConfig) -> list[AvisoConversao]:
    texto = markdown.strip()
    if (
        len(texto) < config.minimo_texto_util
        or texto.count("\ufffd") / max(1, len(texto)) > config.max_proporcao_substituicao
    ):
        return [
            AvisoConversao(
                "baixa_qualidade",
                None,
                "Leitura com pouco texto ou caracteres ilegíveis; confira o original.",
            )
        ]
    return []
