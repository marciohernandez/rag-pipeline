"""Busca de HTML público com destino fixado ao IP validado (SPEC-0036)."""

from __future__ import annotations

import http.client
import ipaddress
import socket
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit, urlunsplit

from src.pipeline.conversion.config import ConversaoConfig
from src.pipeline.conversion.contracts import ConversionUserError


class UrlBloqueadaError(ConversionUserError):
    """Endereço não autorizado para conexão."""


class BuscaFalhouError(ConversionUserError):
    """Erro de busca seguro para exibição."""


@dataclass(frozen=True)
class RespostaHttp:
    status: int
    cabecalhos: dict[str, str]
    corpo: bytes


@dataclass(frozen=True)
class ResultadoBusca:
    html: bytes
    url_final: str


def resolver_padrao(host: str) -> list[str]:
    return list(
        dict.fromkeys(
            item[4][0] for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        )
    )


def _publico(endereco: str) -> bool:
    ip = ipaddress.ip_address(endereco)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast and not ip.is_reserved


def validar_url_publica(url: str, resolver=None) -> str:
    """Valida sintaxe e cada resposta DNS; devolve o IP para a conexão."""
    try:
        if not isinstance(url, str) or any(ord(c) < 33 or ord(c) == 127 for c in url):
            raise ValueError
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 80 if parsed.scheme == "http" else 443)
            or "\\" in url
            or "%" in parsed.hostname
        ):
            raise ValueError
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost"):
            raise ValueError
        try:
            ipaddress.ip_address(host)
            enderecos = [host]
        except ValueError:
            enderecos = (resolver or resolver_padrao)(host)
        if not enderecos or not all(_publico(ip) for ip in enderecos):
            raise ValueError
        return enderecos[0]
    except Exception:  # noqa: BLE001 — DNS e parsing têm erro público sem detalhes
        raise UrlBloqueadaError(
            "Endereço inválido ou não público; use uma página pública http ou https."
        ) from None


def url_sem_segredos(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


def transporte_padrao(url: str, ip: str, timeout: float, max_bytes: int) -> RespostaHttp:
    """Sem proxies/cookies, sem nova resolução; HTTPS preserva SNI e certificado."""
    parsed = urlsplit(url)
    limite = time.monotonic() + timeout
    classe = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
    conexao = classe(parsed.hostname, port=parsed.port, timeout=timeout)

    def conectar(_address, timeout=timeout, source_address=None):
        familia = socket.AF_INET6 if ":" in ip else socket.AF_INET
        sock = socket.socket(familia, socket.SOCK_STREAM)
        try:
            sock.settimeout(timeout)
            sock.connect((ip, parsed.port or (443 if parsed.scheme == "https" else 80)))
            return sock
        except BaseException:
            sock.close()
            raise

    conexao._create_connection = conectar
    try:
        alvo = urlunsplit(("", "", parsed.path or "/", parsed.query, ""))
        conexao.request(
            "GET",
            alvo,
            headers={"Accept": "text/html, application/xhtml+xml", "Accept-Encoding": "identity"},
        )
        resposta = conexao.getresponse()
        cabecalhos = {k.lower(): v for k, v in resposta.getheaders()}
        if 300 <= resposta.status < 400:
            return RespostaHttp(resposta.status, cabecalhos, b"")
        if int(cabecalhos.get("content-length", "0")) > max_bytes:
            raise BuscaFalhouError("A página excede o tamanho permitido.")
        partes = []
        tamanho = 0
        while True:
            restante = limite - time.monotonic()
            if restante <= 0:
                raise TimeoutError
            if conexao.sock:
                conexao.sock.settimeout(restante)
            parte = resposta.read1(min(65536, max_bytes - tamanho + 1))
            if not parte:
                break
            partes.append(parte)
            tamanho += len(parte)
            if tamanho > max_bytes:
                raise BuscaFalhouError("A página excede o tamanho permitido.")
        return RespostaHttp(resposta.status, cabecalhos, b"".join(partes))
    finally:
        conexao.close()


class UrlFetcher:
    def __init__(self, config: ConversaoConfig | None = None, resolver=None, transporte=None):
        self.config = config or ConversaoConfig()
        self.resolver = resolver
        self.transporte = transporte

    def buscar(self, url: str) -> ResultadoBusca:
        atual = url
        limite = time.monotonic() + self.config.timeout_url_s
        try:
            for salto in range(self.config.max_redirecionamentos + 1):
                ip = validar_url_publica(atual, self.resolver)
                restante = limite - time.monotonic()
                if restante <= 0:
                    raise TimeoutError
                resposta = (self.transporte or transporte_padrao)(
                    atual, ip, restante, self.config.max_bytes_url
                )
                headers = {k.lower(): v for k, v in resposta.cabecalhos.items()}
                if resposta.status in {301, 302, 303, 307, 308}:
                    if salto == self.config.max_redirecionamentos or not headers.get("location"):
                        raise BuscaFalhouError("A página excedeu o limite de redirecionamentos.")
                    atual = urljoin(atual, headers["location"])
                    continue
                if not 200 <= resposta.status < 300:
                    raise BuscaFalhouError("Não foi possível buscar a página; tente reenviar.")
                if headers.get("content-type", "").split(";")[0].strip().lower() not in {
                    "text/html",
                    "application/xhtml+xml",
                }:
                    raise BuscaFalhouError(
                        "não consegui extrair o conteúdo: o endereço não é uma página HTML; "
                        "salve o .html pelo navegador e envie-o."
                    )
                if len(resposta.corpo) > self.config.max_bytes_url:
                    raise BuscaFalhouError("A página excede o tamanho permitido.")
                return ResultadoBusca(resposta.corpo, url_sem_segredos(atual))
        except ConversionUserError:
            raise
        except Exception:  # noqa: BLE001 — rede nunca expõe URL ou resposta interna
            raise BuscaFalhouError("Não foi possível buscar a página; tente reenviar.") from None
        raise BuscaFalhouError("Não foi possível buscar a página.")
