"""
Demonstracao do fluxo RAG completo.
Mostra exatamente o que o LLM recebe quando o usuario faz uma pergunta.

A recuperação usa o escopo lógico explícito: `project_id` vem de
`projeto.nome` e `--tenant` é opcional. Sem `--tenant`, apenas registros sem
tenant são alcançados.

Uso:
    uv run python demo_rag.py
    uv run python demo_rag.py --tenant cliente-a "quais informações estão disponíveis?"
"""

import argparse
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.bootstrap import load_env
from src.pipeline.config import load_config
from src.pipeline.indexing import (
    PERGUNTA_NEUTRA,
    BaseIdentity,
    build_embeddings,
    build_scope,
    build_vector_store,
    resolve_default_question,
    resolve_identity,
)
from src.pipeline.providers.contracts import LogicalScope  # noqa: F401  (contrato do escopo)

PERGUNTA_PADRAO = PERGUNTA_NEUTRA


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demonstração do fluxo RAG")
    parser.add_argument("pergunta", nargs="?", default=None)
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument(
        "--tenant",
        default=None,
        help="Escopo lógico do tenant; sem ele apenas registros sem tenant aparecem.",
    )
    parser.add_argument("--config", default="config.yaml")
    return parser.parse_args()


def montar_prompt(
    identidade: BaseIdentity, contexto: str, pergunta: str
) -> str:
    """Monta o prompt demonstrado a partir da configuração da base."""
    return f"""Voce e um assistente especialista na base {identidade.nome}.
A base contém {identidade.descricao}.
Use APENAS as informacoes abaixo para responder.
Se nao souber, diga que nao encontrou nas fontes disponíveis.

=== CONTEXTO ===
{contexto}
================

Pergunta: {pergunta}
Resposta:"""


def main() -> None:
    load_env()
    # Forca UTF-8 no terminal Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    args = parse_args()
    cfg = load_config(args.config)
    identidade = resolve_identity(cfg)
    embedding_cfg = cfg["embedding"]
    vector_cfg = cfg["vector_store"]
    persist_dir = cfg["caminhos"].get("vector_store_dir", "./output/vector_store")

    scope = build_scope(identidade.nome, args.tenant)
    embeddings = build_embeddings(embedding_cfg)
    store = build_vector_store(vector_cfg, persist_dir)

    pergunta = args.pergunta
    if pergunta is None:
        pergunta, _derivada = resolve_default_question(cfg)

    print("\n" + "=" * 65)
    print(f"  PERGUNTA: {pergunta}")
    print(f"  ESCOPO: projeto={scope.project_id} tenant={scope.tenant_id or '(sem tenant)'}")
    print("=" * 65)

    # ─────────────────────────────────────────────────────────────
    # PASSO 1: A pergunta vira vetor e busca no escopo autorizado
    # ─────────────────────────────────────────────────────────────
    print("\n[PASSO 1] Buscando chunks relevantes no escopo autorizado...")
    resultados = store.query(scope, embeddings.embed_query(pergunta), args.k)

    print(f"  {len(resultados)} chunks encontrados:\n")
    for i, resultado in enumerate(resultados, 1):
        nome = resultado.metadata.get("nome_arquivo", "?")
        secao = resultado.metadata.get("secao", "")
        print(f"  #{i} score={resultado.score:.3f} | {nome}" + (f" › {secao}" if secao else ""))

    # ─────────────────────────────────────────────────────────────
    # PASSO 2: Monta o contexto que vai para o LLM
    # ─────────────────────────────────────────────────────────────
    print("\n[PASSO 2] Montando o contexto com o conteúdo dos chunks...")

    blocos_contexto = []
    for resultado in resultados:
        nome = resultado.metadata.get("nome_arquivo", "?")
        secao = resultado.metadata.get("secao", "")
        cabecalho = f"[Fonte: {nome}" + (f" › {secao}]" if secao else "]")
        blocos_contexto.append(f"{cabecalho}\n{resultado.content}")

    contexto = "\n\n---\n\n".join(blocos_contexto)

    # ─────────────────────────────────────────────────────────────
    # PASSO 3: O prompt completo que o LLM receberia
    # ─────────────────────────────────────────────────────────────
    prompt = montar_prompt(identidade, contexto, pergunta)

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


if __name__ == "__main__":
    main()
