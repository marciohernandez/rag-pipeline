# Backlog: Fase 1: detectar contradições entre documentos e gerar relatório com origem

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0042 |
| Status | Refining |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-09 |
| Spec promovida | Nenhuma |

## Ideia original

analisar todos os .md, achar informações contraditórias e gerar relatório com os arquivos de origem para conferir com a empresa (mensagens de 2026-10-09)

## Problema percebido

Áreas diferentes da mesma empresa dão informações conflitantes (ex.: cancelamento 7 dias no comercial e 15 no marketing; preços e descontos) e o RAG responderia de forma incoerente.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Relatório das contradições, cada uma com os arquivos e trechos de origem, para a empresa decidir o que vale.

## Contexto

Fase 1 do rag-pipeline (PROJECT.md:6): hoje o envio só aceita .md (src/app/ingestao.py) e src/pipeline/conversion/converters está vazio. Capturas: specs/inbox/2026-10-09-192547-*.md e 2026-10-09-194532-*.md. Entradas variam: PDF (inclusive prints de PPT/PPTX e fotos), Google Docs/Planilhas, XLS, imagens JPG/PNG (conversas, apresentações, telas de app; podem ou não ser sequência), URLs. Áreas: comercial, atendimento, RH, marketing, diretoria. Saída: .md limpos, sem contradições nem duplicidade, prontos para a Fase 2. Contrato do .md: SPEC-0002. Dividido em 5 backlogs por decisão do usuário em 2026-10-09 (Pergunta 1, opção 1).

## Referências relacionadas

- `specs/inbox/2026-10-09-192547-receber-documentos-em-varios-formatos-e-extrair-informacoes-para-gerar-os-markdown-de-processamento.md` — origem (captura).
- `specs/inbox/2026-10-09-194532-fase-1-receber-documentos-extrair-o-conteudo-de-dominio-gerar-markdown-e-relatar-contradicoes.md` — origem (captura detalhada).
- `specs/completed/0002-compatibilizar-o-contrato-markdown-do-projeto-mae/spec.md` — spec relacionada: contrato do Markdown de saída.
- `specs/completed/0030-colecoes-por-workspace-com-envios-acumulados/spec.md` — spec relacionada: envio atual, só `.md`.
- `PROJECT.md` (linhas 6 e 166) — documentação: Fase 1 fora do componente atual.
- Backlogs irmãos da Fase 1: 0039 a 0043 (dividido em 5 por decisão do usuário em 2026-10-09).

## Comportamento esperado

- Comparar os `.md` entre si e detectar contradições e duplicidade (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Gerar relatório `.md` baixável com os documentos em conflito e a divergência exata, com arquivos e trechos de origem.
- Exemplo do usuário: política de cancelamento de 7 dias no comercial e 15 no marketing; preços e descontos.

## Regras de negócio

- O relatório serve para conferir com a empresa o que vale; não corrige nada sozinho.

## Critérios de aceitação

- A esclarecer antes de considerar o item refinado.

## Qualidades e operação

- Segurança: a avaliar.
- Privacidade: a avaliar.
- Desempenho e volume: a avaliar.
- Auditoria e observabilidade: a avaliar.

## Dependências

- Nenhuma registrada.

## Situações de erro

- A esclarecer.

## Escopo

- Dentro: análise cruzada e relatório.
- Fora: aplicar correções (0043).

## Dúvidas, decisões e riscos

- Critério de contradição (numérica, de política, de versão).
- Meta do briefing: ≥90% das contradições reais capturadas, medido contra amostra revisada manualmente; confirmar se vale.
- Escala: comparar todos contra todos.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
