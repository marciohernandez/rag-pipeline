# Backlog: Provider plugável de LLM de chat/geração

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0010 |
| Status | Captured |
| Produto | RAG Pipeline SaaS |
| Épico | Finalizar o componente rag-ingestion-pipeline |
| Funcionalidade | Arquitetura de providers |
| Tipo | Técnico |
| Prioridade | P3 — baixa |
| Milestones | M0 — Finalizar o componente rag-ingestion-pipeline |
| Criado em | 2026-09-01 |
| Spec promovida | Nenhuma |

## Ideia original

Aplicar o padrão plug and play do BACKLOG-0003 à terceira família de provider: o LLM de chat/geração usado pelo RAG. Hoje `chat.py` instancia `ChatOpenAI` diretamente (`chat.py:20`), sem contrato, factory ou possibilidade de troca por configuração.

## Problema percebido

O objetivo declarado é um sistema plug and play para toda família de provider — banco vetorial, embeddings e LLM. O BACKLOG-0003 entrega o soquete para embeddings e vector stores, mas deixa o LLM de chat fora do escopo. Enquanto isso não for feito, trocar o modelo de resposta (para um LLM local, outro fornecedor, ou um modelo diferente) exige editar código.

## Pessoa afetada ou beneficiada

Mantenedores do componente e quem, no futuro, quiser operar o RAG com um LLM diferente do OpenAI.

## Resultado ou valor esperado

Um contrato `LLMProvider` neutro, um adapter OpenAI e uma factory, com `chat.py` compondo o provider a partir da configuração. Trocar ou adicionar um LLM passa a ser implementar o contrato + registrar na factory + configurar.

## Contexto

- Depende do padrão (contratos, factory, capability flags, suíte de conformidade, adapter fake) estabelecido por BACKLOG-0003; não começa antes disso.
- `chat.py` é um CLI de demonstração, não caminho crítico do pipeline — daí a prioridade baixa.
- Escopo da configuração de LLM (parâmetros como `model`, `temperature`, streaming) a definir no refinamento; hoje o `config.yaml` não tem seção de LLM.

## Referências relacionadas

- `specs/backlog/0003-modularizar-providers-factory-adapter.md` — estabelece o padrão plug and play e o `src/providers/`. Tipo: pré-requisito.
- `chat.py` — consumidor atual com `ChatOpenAI` hardcoded. Tipo: superfície afetada.
- `.specsfy/RULES.md` (Arquitetura) — Factory/Adapter para providers, LangGraph/LangChain v1-first para orquestração de IA. Tipo: regra do projeto.
- `.agents/skills/specsfy-specialist-langchain` — orienta o desenho do adapter sobre LangChain v1. Tipo: especialista.

## Comportamento esperado

A esclarecer no refinamento. Direção inicial: `src/providers/llm/` com `base.py`, `openai.py` e `fake.py`; factory por nome; `chat.py` obtém o provider da configuração; nenhum import de SDK de LLM fora de `src/providers/`.

## Regras de negócio

- A esclarecer. Preservar o comportamento atual do chat RAG; não introduzir dependência nova sem confirmação; seguir LangChain v1.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: credenciais do LLM lidas apenas dentro do adapter, nunca na factory; nenhum segredo no repositório.
- Privacidade: avaliar no refinamento (envio de conteúdo a provider externo já ocorre hoje via `ChatOpenAI`).
- Desempenho: sem regressão perceptível no chat CLI.
- Observabilidade: a definir.

## Dependências

- BACKLOG-0003 concluído (padrão plug and play, `src/providers/`, suíte de conformidade).

## Situações de erro

- A esclarecer. Incluir provider desconhecido (factory) e credencial ausente (adapter, na inicialização), sem chamada remota.

## Escopo

- Dentro: contrato `LLMProvider`, adapter OpenAI, fake determinístico, factory, migração de `chat.py`, seção de LLM no `config.yaml` se necessária.
- Fora: novos providers de LLM em produção; orquestração agentic/LangGraph; qualquer coisa do projeto-mãe.

## Dúvidas, decisões e riscos

- Decisão herdada de BACKLOG-0003 (Pergunta 13): a família de LLM ficou fora da fatia de modularização para não elevar o Effort; este item aplica o mesmo padrão depois.
- Risco: pode ser fechado como "não será feito" se o chat CLI deixar de ser relevante após a consolidação no `rag-pipeline`.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Manter capturado até BACKLOG-0003 ser concluído. Refinar com `$specsfy-02-backlog` quando o padrão plug and play existir e houver intenção de trocar o LLM.
