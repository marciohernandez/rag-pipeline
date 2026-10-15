"""Coletor descartável de avisos do ensaio local; nunca usar em produção."""

import socketserver
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class SMTP(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"220 local SMTP\r\n")
        while linha := self.rfile.readline():
            comando = linha.decode().strip().upper()
            if comando.startswith("EHLO"):
                self.wfile.write(b"250-local\r\n250 AUTH PLAIN LOGIN\r\n")
            elif comando.startswith("AUTH"):
                # Somente credenciais fictícias; não registrar o conteúdo.
                if comando == "AUTH LOGIN":
                    self.wfile.write(b"334 VXNlcm5hbWU6\r\n")
                    self.rfile.readline()
                    self.wfile.write(b"334 UGFzc3dvcmQ6\r\n")
                    self.rfile.readline()
                elif comando == "AUTH PLAIN":
                    self.wfile.write(b"334 \r\n")
                    self.rfile.readline()
                self.wfile.write(b"235 OK\r\n")
            elif comando == "DATA":
                self.wfile.write(b"354 data\r\n")
                while self.rfile.readline() not in (b".\r\n", b""):
                    pass
                print("AVISO smtp recebido", flush=True)
                self.wfile.write(b"250 OK\r\n")
            elif comando == "QUIT":
                self.wfile.write(b"221 bye\r\n")
                break
            else:
                self.wfile.write(b"250 OK\r\n")


class Webhook(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        print("AVISO webhook recebido", flush=True)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    servidor = socketserver.ThreadingTCPServer(("0.0.0.0", 1025), SMTP)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    ThreadingHTTPServer(("0.0.0.0", 8080), Webhook).serve_forever()
