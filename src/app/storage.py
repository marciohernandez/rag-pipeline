"""Armazenamento dos arquivos Markdown enviados (SPEC-0012, seção 8).

Duas implementações do mesmo protocolo: ``S3CompatibleStorage`` fala com o
Cloudflare R2 (compatível S3) via ``boto3`` quando as credenciais estão
configuradas, e ``LocalDirectoryStorage`` grava em um diretório local — usada
por padrão em desenvolvimento/teste quando nenhuma credencial de R2 é
fornecida. Nenhuma das duas lê ``config.yaml`` ou variável de ambiente
diretamente: o entrypoint decide qual instanciar e injeta o resultado.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Protocol

__all__ = [
    "LocalDirectoryStorage",
    "S3CompatibleStorage",
    "Storage",
    "configure",
    "get_storage",
]


class Storage(Protocol):
    def save(self, base_id: str, filename: str, content: bytes) -> str:
        """Salva um arquivo da base e devolve sua chave de armazenamento."""

    def delete_base(self, base_id: str) -> None:
        """Remove todos os arquivos armazenados de uma base."""

    def materialize(self, base_id: str, target_dir: str | Path) -> None:
        """Copia os arquivos da base para ``target_dir`` local, para o pipeline ler."""

    def list_files(self, base_id: str) -> list[str]:
        """Lista os nomes de arquivo armazenados sob ``base_id``."""


class LocalDirectoryStorage:
    """Grava os arquivos em um diretório local. Padrão fora de produção."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def save(self, base_id: str, filename: str, content: bytes) -> str:
        pasta = self._root / base_id
        pasta.mkdir(parents=True, exist_ok=True)
        destino = pasta / filename
        destino.write_bytes(content)
        return str(destino.relative_to(self._root))

    def delete_base(self, base_id: str) -> None:
        pasta = self._root / base_id
        if pasta.exists():
            shutil.rmtree(pasta)

    def materialize(self, base_id: str, target_dir: str | Path) -> None:
        origem = self._root / base_id
        destino = Path(target_dir)
        destino.mkdir(parents=True, exist_ok=True)
        if origem.exists():
            for arquivo in origem.glob("*"):
                if arquivo.is_file():
                    shutil.copy2(arquivo, destino / arquivo.name)

    def list_files(self, base_id: str) -> list[str]:
        pasta = self._root / base_id
        if not pasta.exists():
            return []
        return [arquivo.name for arquivo in pasta.glob("*") if arquivo.is_file()]


class S3CompatibleStorage:
    """Cliente S3-compatível para o Cloudflare R2."""

    def __init__(self, *, bucket: str, endpoint_url: str, access_key: str, secret_key: str) -> None:
        import boto3

        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

    def save(self, base_id: str, filename: str, content: bytes) -> str:
        key = f"{base_id}/{filename}"
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content)
        return key

    def delete_base(self, base_id: str) -> None:
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=f"{base_id}/"):
            for item in page.get("Contents", []):
                self._client.delete_object(Bucket=self._bucket, Key=item["Key"])

    def materialize(self, base_id: str, target_dir: str | Path) -> None:
        destino = Path(target_dir)
        destino.mkdir(parents=True, exist_ok=True)
        paginator = self._client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=f"{base_id}/"):
            for item in page.get("Contents", []):
                nome = item["Key"].split("/", 1)[-1]
                objeto = self._client.get_object(Bucket=self._bucket, Key=item["Key"])
                (destino / nome).write_bytes(objeto["Body"].read())

    def list_files(self, base_id: str) -> list[str]:
        paginator = self._client.get_paginator("list_objects_v2")
        return [
            item["Key"].split("/", 1)[-1]
            for page in paginator.paginate(Bucket=self._bucket, Prefix=f"{base_id}/")
            for item in page.get("Contents", [])
        ]


_STORAGE: Storage | None = None


def configure(storage: Storage) -> None:
    global _STORAGE
    _STORAGE = storage


def get_storage() -> Storage:
    if _STORAGE is None:
        raise RuntimeError(
            "Storage não configurado. Chame src.app.storage.configure(...) no entrypoint."
        )
    return _STORAGE
