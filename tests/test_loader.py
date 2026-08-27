from pathlib import Path

import pytest

from src.loader import DocumentLoadError, load_markdown_documents


def test_loader_adds_source_hash(tmp_path: Path) -> None:
    source = tmp_path / "documento.md"
    source.write_text("# Título\n\nConteúdo", encoding="utf-8")

    [document] = load_markdown_documents(str(tmp_path))

    assert document.metadata["source_hash"]
    assert len(document.metadata["source_hash"]) == 64


def test_loader_fails_fast_when_a_source_is_invalid(tmp_path: Path) -> None:
    (tmp_path / "válido.md").write_text("# Válido", encoding="utf-8")
    (tmp_path / "inválido.md").write_bytes(b"\xff\xfe")

    with pytest.raises(DocumentLoadError, match="indexação cancelada"):
        load_markdown_documents(str(tmp_path))
