"""
RAG Chat — Modo Interativo
Busca informações no Qdrant e usa um LLM (via OpenRouter) para responder as perguntas.

Uso:
    uv run python chat.py
"""

import argparse
import os
import sys
import io
from pathlib import Path

# Forca UTF-8 no terminal Windows para evitar UnicodeEncodeError
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.config import load_config
from src.indexing import build_embeddings, build_scope, build_vector_store
from src.providers.contracts import LogicalScope  # noqa: F401  (contrato do escopo)

def format_docs(results):
    """
    Formata os resultados recuperados para passar ao LLM.
    Inclui o 'breadcrumb' de onde o chunk veio (salvo no passo de chunker).
    """
    blocos = []
    for r in results:
        fonte = r.metadata.get("nome_arquivo", "?")
        # O proprio content ja tem o breadcrumb injetado, mas
        # reforcamos aqui a indicacao da fonte do arquivo.
        blocos.append(f"[Fonte: {fonte}]\n{r.content}")
    return "\n\n---\n\n".join(blocos)

def parse_args():
    parser = argparse.ArgumentParser(description="Chat RAG na base vetorial")
    parser.add_argument("--k", type=int, default=4, help="Chunks recuperados por pergunta")
    parser.add_argument(
        "--tenant",
        default=None,
        help=(
            "Escopo lógico do tenant. Sem este argumento a recuperação alcança "
            "somente registros sem tenant."
        ),
    )
    parser.add_argument("--config", default="config.yaml")
    return parser.parse_args()

def main():
    load_dotenv()
    args = parse_args()
    cfg = load_config(args.config)

    # 1. Configura embeddings, vector store e o escopo lógico explícito
    print("Iniciando RAG C6 Empresas...")
    embedding_cfg = cfg.get("embedding", {})
    vector_cfg = cfg.get("vector_store", {})
    persist_dir = cfg.get("caminhos", {}).get("vector_store_dir", "./output")

    scope = build_scope(cfg["projeto"]["nome"], args.tenant)
    embeddings = build_embeddings(embedding_cfg)
    store = build_vector_store(vector_cfg, persist_dir)
    print(
        f"Escopo: projeto={scope.project_id} "
        f"tenant={scope.tenant_id or '(sem tenant)'}"
    )

    def retrieve(pergunta: str):
        """Recupera somente dentro do escopo autorizado, sem filtro de SDK."""
        return store.query(scope, embeddings.embed_query(pergunta), args.k)

    retriever = RunnableLambda(retrieve)

    # 2. Configura o LLM via OpenRouter
    llm_model = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
    print(f"Modelo configurado: {llm_model}")
    
    llm = ChatOpenAI(
        model=llm_model,
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.0
    )
    
    # 3. Prompt Template
    template = """Você é um assistente especialista nos produtos do C6 Bank Empresas.
Use o contexto abaixo para responder a pergunta do usuário de forma clara, prestativa e precisa.
Sempre que possível, cite a fonte (nome do arquivo ou seção) de onde tirou a informação.
Se a informação não estiver no contexto, diga claramente que não encontrou nos manuais disponíveis e não invente respostas.

=== CONTEXTO DISPONÍVEL ===
{context}
===========================

Pergunta do Usuário: {question}
Sua Resposta:"""
    prompt = ChatPromptTemplate.from_template(template)
    
    # 4. Cadeia RAG (Chain)
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("\n" + "="*50)
    print("🤖 CHATBOT RAG C6 EMPRESAS PRONTO!")
    print("Digite 'sair' para encerrar.")
    print("="*50 + "\n")
    
    while True:
        try:
            pergunta = input("\nVocê: ")
            if pergunta.lower().strip() in ['sair', 'exit', 'quit']:
                break
            if not pergunta.strip():
                continue
                
            print("\n🤖 Assistente (pesquisando manuais...):")
            
            # Executa a busca e gera a resposta iterando pelos chunks em streaming para ficar mais rapido visualmente
            for chunk in rag_chain.stream(pergunta):
                print(chunk, end="", flush=True)
            print("\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n❌ Ocorreu um erro: {e}")

if __name__ == "__main__":
    main()
