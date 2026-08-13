"""
RAG Chat — Modo Interativo
Busca informações no Qdrant e usa um LLM (via OpenRouter) para responder as perguntas.

Uso:
    uv run python chat.py
"""

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
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from src.config import load_config
from src.embedder import get_embeddings, get_vector_store

def format_docs(docs):
    """
    Formata os chunks recuperados para passar ao LLM.
    Inclui o 'breadcrumb' de onde o chunk veio (salvo no passo de chunker).
    """
    blocos = []
    for d in docs:
        fonte = d.metadata.get("nome_arquivo", "?")
        breadcrumb = d.metadata.get("breadcrumb", "")
        # O proprio page_content ja tem o breadcrumb injetado, mas 
        # reforcamos aqui a indicacao da fonte do arquivo.
        blocos.append(f"[Fonte: {fonte}]\n{d.page_content}")
    return "\n\n---\n\n".join(blocos)

def main():
    load_dotenv()
    cfg = load_config()
    
    # 1. Configura embeddings e vector store
    print("Iniciando RAG C6 Empresas...")
    embedding_cfg = cfg.get("embedding", {})
    vector_cfg = cfg.get("vector_store", {})
    
    embeddings = get_embeddings(embedding_cfg)
    store = get_vector_store(vector_cfg, embeddings, persist_dir="./output")
    retriever = store.as_retriever(search_kwargs={"k": 4})
    
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
