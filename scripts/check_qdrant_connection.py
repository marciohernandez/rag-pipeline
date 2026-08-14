"""Verifica a conexao e a leitura de uma collection Qdrant via REST."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


COLLECTION = "vivo_gold_banda_larga_pf"
TIMEOUT_SECONDS = 15


def load_env(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def request_json(base_url: str, api_key: str, path: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"api-key": api_key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"

    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.load(response)


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_env(project_root / ".env")

    base_url = os.getenv("QDRANT_URL", "").strip()
    api_key = os.getenv("QDRANT_API_KEY", "").strip()
    parsed_url = urlparse(base_url)

    print(f"Host configurado: {parsed_url.hostname or '<invalido>'}", flush=True)
    print(f"Chave presente: {bool(api_key)}", flush=True)

    if parsed_url.scheme not in {"http", "https"} or not parsed_url.hostname:
        print("Configuracao invalida: QDRANT_URL deve ser uma URL HTTP(S).")
        return 2
    if not api_key:
        print("Configuracao invalida: QDRANT_API_KEY nao foi definida.")
        return 2

    try:
        collections_response = request_json(base_url, api_key, "/collections")
        collections = [
            item["name"]
            for item in collections_response.get("result", {}).get("collections", [])
        ]
        print("Conexao: OK")
        print(f"Colecoes encontradas: {len(collections)}")
        print(f"Colecao Vivo existe: {COLLECTION in collections}")

        if COLLECTION not in collections:
            print("Colecoes disponiveis: " + ", ".join(collections))
            return 1

        count_response = request_json(
            base_url,
            api_key,
            f"/collections/{COLLECTION}/points/count",
            {"exact": True},
        )
        count = count_response.get("result", {}).get("count", 0)
        print(f"Pontos na Vivo: {count}")

        scroll_response = request_json(
            base_url,
            api_key,
            f"/collections/{COLLECTION}/points/scroll",
            {"limit": 1, "with_payload": True, "with_vector": False},
        )
        points = scroll_response.get("result", {}).get("points", [])
        payload = points[0].get("payload", {}) if points else {}
        print(f"Payload recuperado: {bool(payload)}")
        print("Campos: " + ", ".join(sorted(payload)))

        content = next(
            (
                payload.get(field)
                for field in ("page_content", "text", "content", "document")
                if payload.get(field)
            ),
            "",
        )
        snippet = " ".join(str(content).split())[:500]
        print(f"Trecho: {snippet or '<campo textual nao identificado>'}")
        return 0
    except HTTPError as error:
        print(f"Conexao: FALHOU (HTTP {error.code})")
        if error.code in {401, 403}:
            print("Diagnostico: credencial ausente, invalida ou sem permissao.")
        return 1
    except URLError as error:
        print(f"Conexao: FALHOU ({error.reason})")
        return 1
    except TimeoutError:
        print(f"Conexao: FALHOU (timeout de {TIMEOUT_SECONDS}s)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
