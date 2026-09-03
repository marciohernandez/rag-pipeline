import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from src.chunker import chunk_documents
from src.loader import load_markdown_documents

docs = load_markdown_documents('./arquivos processados')
chunks = chunk_documents(docs, {})

# Mostra chunks de arquivos diferentes para ver o breadcrumb
exemplos_indices = [3, 10, 31, 60]
for i in exemplos_indices:
    if i >= len(chunks):
        continue
    c = chunks[i]
    print("=" * 60)
    print(f"CHUNK #{i} | {c.metadata.get('nome_arquivo')}")
    print(f"breadcrumb no metadata: {c.metadata.get('breadcrumb', 'nenhum')}")
    print()
    print("[page_content - primeiras 3 linhas]")
    linhas = c.page_content.strip().splitlines()
    for linha in linhas[:4]:
        print(" ", linha)
    print()
