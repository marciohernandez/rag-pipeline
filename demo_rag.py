"""
Demonstracao do fluxo RAG completo.
Mostra exatamente o que o LLM recebe quando o usuario faz uma pergunta.

Uso:
    uv run python demo_rag.py
"""

import sys
import io
from pathlib import Path

# Forca UTF-8 no terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from src.config import load_config
from src.embedder import get_embeddings, get_vector_store

cfg = load_config()
embedding_cfg = cfg["embedding"]
vector_cfg = cfg["vector_store"]
persist_dir = cfg["caminhos"].get("vector_store_dir", "./output/chroma_db")

embeddings = get_embeddings(embedding_cfg)
store = get_vector_store(vector_cfg, embeddings, persist_dir)

# ─────────────────────────────────────────────────────────────
# PERGUNTA DO USUARIO
# ─────────────────────────────────────────────────────────────
pergunta = "qual a taxa do cheque especial?"

print("\n" + "=" * 65)
print(f"  PERGUNTA: {pergunta}")
print("=" * 65)

# ─────────────────────────────────────────────────────────────
# PASSO 1: A pergunta vira vetor e busca no Qdrant
# ─────────────────────────────────────────────────────────────
print("\n[PASSO 1] Buscando chunks relevantes no Qdrant...")
resultados = store.similarity_search_with_score(pergunta, k=3)

print(f"  {len(resultados)} chunks encontrados:\n")
for i, (doc, score) in enumerate(resultados, 1):
    nome = doc.metadata.get("nome_arquivo", "?")
    secao = doc.metadata.get("secao", "")
    print(f"  #{i} score={score:.3f} | {nome}" + (f" › {secao}" if secao else ""))

# ─────────────────────────────────────────────────────────────
# PASSO 2: Monta o contexto que vai para o LLM
# ─────────────────────────────────────────────────────────────
print("\n[PASSO 2] Montando o contexto com os page_content dos chunks...")

blocos_contexto = []
for doc, score in resultados:
    nome = doc.metadata.get("nome_arquivo", "?")
    secao = doc.metadata.get("secao", "")
    cabecalho = f"[Fonte: {nome}" + (f" › {secao}]" if secao else "]")
    blocos_contexto.append(f"{cabecalho}\n{doc.page_content}")

contexto = "\n\n---\n\n".join(blocos_contexto)

# ─────────────────────────────────────────────────────────────
# PASSO 3: O prompt completo que o LLM receberia
# ─────────────────────────────────────────────────────────────
prompt = f"""Voce e um assistente especialista em C6 Bank Empresas.
Use APENAS as informacoes abaixo para responder.
Se nao souber, diga que nao encontrou nas fontes disponíveis.

=== CONTEXTO ===
{contexto}
================

Pergunta: {pergunta}
Resposta:"""

print("\n[PASSO 3] Prompt completo que o LLM recebe:")
print("-" * 65)
print(prompt)
print("-" * 65)

# ─────────────────────────────────────────────────────────────
# PASSO 4: LLM gera a resposta (simulado — so mostra o prompt)
# ─────────────────────────────────────────────────────────────
print("\n[PASSO 4] Aqui o LLM leria o CONTEXTO e geraria a resposta.")
print("  O metadata (nome_arquivo, secao, topic) NAO vai para o LLM.")
print("  Voce usa o metadata no codigo para exibir 'Fonte: arquivo.md'")
print("  junto com a resposta para o usuario final.\n")
