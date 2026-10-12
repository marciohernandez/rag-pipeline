"""Regras de domínio das conexões de ingestão (SPEC-0026).

Concentra o que não depende de HTTP nem de banco: validação de nome, tipo,
configuração e URL, cifra da chave com Fernet, máscara fixa e a montagem da
configuração entregue à fachada do pipeline. A chave de cifra chega pelo
entrypoint (``AppSettings.conexoes_chave``); nada aqui lê o ambiente.
"""

from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken

__all__ = [
    "MASCARA",
    "TIPOS",
    "TIPO_EMBEDDINGS",
    "TIPO_QDRANT",
    "ErroDeConexao",
    "cifrar_segredo",
    "configuracao_para_pipeline",
    "decifrar_segredo",
    "serializar_conexao",
    "testar_conexao_salva",
    "validar_configuracao",
    "validar_nome",
    "validar_tipo",
    "validar_url",
]

MASCARA = "••••••••"
TIPO_EMBEDDINGS = "embeddings_openai"
TIPO_QDRANT = "qdrant"
TIPOS = (TIPO_EMBEDDINGS, TIPO_QDRANT)
MODELO_PADRAO = "text-embedding-3-small"
DIMENSOES_PADRAO = 1536
DIMENSOES_MAXIMAS = 20000
TAMANHO_MAXIMO_NOME = 80
_HOSTS_DE_METADADOS = frozenset({"metadata.google.internal", "metadata.goog"})


class ErroDeConexao(Exception):
    """Falha de validação ou de configuração, com o status HTTP a devolver."""

    def __init__(self, detalhe: str, status_code: int = 422) -> None:
        super().__init__(detalhe)
        self.detalhe = detalhe
        self.status_code = status_code


def validar_nome(nome: Any) -> str:
    texto = nome.strip() if isinstance(nome, str) else ""
    if not texto:
        raise ErroDeConexao("Informe o nome da conexão.")
    if len(texto) > TAMANHO_MAXIMO_NOME:
        raise ErroDeConexao(f"O nome da conexão aceita até {TAMANHO_MAXIMO_NOME} caracteres.")
    return texto


def validar_tipo(tipo: Any) -> str:
    if tipo not in TIPOS:
        raise ErroDeConexao("Tipo de conexão desconhecido. Use embeddings_openai ou qdrant.")
    return tipo


def _host_proibido(host: str) -> bool:
    nome = host.lower().rstrip(".")
    if nome == "localhost" or nome.endswith(".localhost") or nome in _HOSTS_DE_METADADOS:
        return True
    try:
        endereco = ipaddress.ip_address(nome)
    except ValueError:
        return False
    return endereco.is_loopback or endereco.is_link_local or endereco.is_unspecified


def validar_url(url: Any, *, permitir_locais: bool = False) -> str:
    """Aceita só http/https sem credenciais e sem hosts internos sensíveis."""
    texto = url.strip() if isinstance(url, str) else ""
    if not texto:
        raise ErroDeConexao("Informe a URL.")
    try:
        partes = urlsplit(texto)
        host = partes.hostname
        partes.port  # noqa: B018 — valida a porta
    except ValueError as erro:
        raise ErroDeConexao("A URL informada é inválida.") from erro
    if partes.scheme not in {"http", "https"} or not host:
        raise ErroDeConexao("A URL deve usar http ou https e informar o host.")
    if partes.username or partes.password:
        raise ErroDeConexao("A URL não pode conter usuário ou senha.")
    if not permitir_locais and _host_proibido(host):
        raise ErroDeConexao("A URL aponta para um endereço interno não permitido.")
    return texto


def validar_configuracao(
    tipo: str, configuracao: Any, *, permitir_locais: bool = False
) -> dict[str, Any]:
    """Normaliza a configuração não secreta e recusa campos desconhecidos."""
    if not isinstance(configuracao, dict):
        raise ErroDeConexao("A configuração da conexão é inválida.")
    permitidos = {"url"} if tipo == TIPO_QDRANT else {"modelo", "url_base", "dimensoes"}
    desconhecidos = sorted(set(configuracao) - permitidos)
    if desconhecidos:
        raise ErroDeConexao(f"Campos desconhecidos na configuração: {', '.join(desconhecidos)}.")
    if tipo == TIPO_QDRANT:
        return {"url": validar_url(configuracao.get("url"), permitir_locais=permitir_locais)}
    modelo = configuracao.get("modelo", MODELO_PADRAO)
    modelo = modelo.strip() if isinstance(modelo, str) else ""
    if not modelo:
        raise ErroDeConexao("Informe o modelo de embeddings.")
    dimensoes = configuracao.get("dimensoes", DIMENSOES_PADRAO)
    if isinstance(dimensoes, bool) or not isinstance(dimensoes, int) or dimensoes < 1:
        raise ErroDeConexao("As dimensões devem ser um inteiro maior que zero.")
    if dimensoes > DIMENSOES_MAXIMAS:
        raise ErroDeConexao(f"As dimensões aceitam até {DIMENSOES_MAXIMAS}.")
    normalizada: dict[str, Any] = {"modelo": modelo, "dimensoes": dimensoes}
    url_base = configuracao.get("url_base")
    if url_base not in (None, ""):
        normalizada["url_base"] = validar_url(url_base, permitir_locais=permitir_locais)
    return normalizada


def _fernet(chave: str) -> Fernet:
    if not chave:
        raise ErroDeConexao("A chave de cifra das conexões não está configurada.", 503)
    try:
        return Fernet(chave.encode())
    except (ValueError, TypeError) as erro:
        raise ErroDeConexao("A chave de cifra das conexões é inválida.", 503) from erro


def cifrar_segredo(chave: str, segredo: str) -> str:
    return _fernet(chave).encrypt(segredo.encode()).decode()


def decifrar_segredo(chave: str, texto: str) -> str:
    try:
        return _fernet(chave).decrypt(texto.encode()).decode()
    except InvalidToken as erro:
        raise ErroDeConexao("Não foi possível decifrar a chave da conexão.", 503) from erro


def configuracao_para_pipeline(
    tipo: str,
    configuracao: dict[str, Any],
    segredo: str | None,
    *,
    collection_name: str | None = None,
    permitir_locais: bool = False,
) -> dict[str, Any]:
    """Monta a seção ``embedding`` ou ``vector_store`` da fachada do pipeline.

    Revalida a configuração: a conexão pode ter sido alterada depois do cadastro.
    """
    valida = validar_configuracao(tipo, configuracao, permitir_locais=permitir_locais)
    if tipo == TIPO_QDRANT:
        resultado: dict[str, Any] = {"provider": "qdrant", "url": valida["url"]}
        if collection_name:
            resultado["collection_name"] = collection_name
    else:
        resultado = {
            "provider": "openai",
            "model": valida["modelo"],
            "dimensions": valida["dimensoes"],
        }
        if valida.get("url_base"):
            resultado["base_url"] = valida["url_base"]
    if segredo:
        resultado["api_key"] = segredo
    return resultado


def testar_conexao_salva(
    conexao: Any, chave_de_cifra: str, *, permitir_locais: bool
) -> dict[str, Any]:
    """Testa uma conexão já gravada pela fachada; nunca impede o salvamento (SPEC-0029)."""
    import src.pipeline.service as service  # noqa: PLR0402 — nome exigido pelo teste de fronteira

    try:
        segredo = (
            decifrar_segredo(chave_de_cifra, conexao.segredo_cifrado)
            if conexao.segredo_cifrado
            else None
        )
        configuracao = configuracao_para_pipeline(
            conexao.tipo, conexao.configuracao, segredo, permitir_locais=permitir_locais
        )
    except ErroDeConexao as erro:
        return {"sucesso": False, "mensagem": erro.detalhe}
    return service.testar_conexao(configuracao)


def serializar_conexao(conexao: Any, em_uso: int) -> dict[str, Any]:
    """Resposta pública: nunca inclui a chave nem o texto cifrado."""
    definido = bool(conexao.segredo_cifrado)
    return {
        "id": conexao.id,
        "nome": conexao.nome,
        "tipo": conexao.tipo,
        "situacao": conexao.situacao,
        "configuracao": dict(conexao.configuracao or {}),
        "segredo_definido": definido,
        "segredo_mascara": MASCARA if definido else "",
        "em_uso": em_uso,
        "criado_por": conexao.criado_por,
        "criado_em": conexao.criado_em.isoformat() if conexao.criado_em else None,
        "atualizada_em": conexao.atualizada_em.isoformat() if conexao.atualizada_em else None,
    }
