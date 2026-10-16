"""Transporte real, com socket simulado: IP fixo, Host e TLS preservados."""

import io
import socket
import ssl

from src.pipeline.conversion.url_fetcher import transporte_padrao


def test_transporte_https_fixa_ip_sem_resolver_e_preserva_sni(monkeypatch):
    """SPECSFY: SPEC-0036 US-001 FR-002 NFR-001 AC-006"""
    destinos, enviados, tls = [], [], []

    class Socket:
        def setsockopt(self, *args):
            pass

        def settimeout(self, valor):
            pass

        def connect(self, destino):
            destinos.append(destino)

        def sendall(self, conteudo):
            enviados.append(conteudo)

        def makefile(self, *args):
            return io.BytesIO(
                b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\nContent-Type: text/html\r\n\r\nbody"
            )

        def close(self):
            pass

    def wrap(context, sock, *, server_hostname):
        assert context.check_hostname and context.verify_mode == ssl.CERT_REQUIRED
        tls.append(server_hostname)
        return sock

    def dns(*args, **kwargs):
        raise AssertionError("Segunda resolução não permitida")

    monkeypatch.setattr(socket, "socket", lambda *args: Socket())
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", wrap)
    resultado = transporte_padrao("https://exemplo.com/p?q=1", "93.184.216.34", 2, 100)
    assert resultado.corpo == b"body"
    assert destinos == [("93.184.216.34", 443)]
    assert tls == ["exemplo.com"]
    assert b"Host: exemplo.com\r\n" in b"".join(enviados)
