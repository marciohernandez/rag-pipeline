# Backlog: Fase 1: detectar e reagrupar sequências de imagens e páginas e montar tabelas

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0040 |
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

prints podem ou não ser uma sequência (conversas, passo a passo de app, slides); organizar sequências e montar tabelas em Markdown (mensagens de 2026-10-09)

## Problema percebido

Imagens e páginas soltas perdem a ordem e o agrupamento; várias conversas ou tutoriais chegam misturados, e tabelas se perdem na extração.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Sequências são reconhecidas e reagrupadas de forma genérica, imagens isoladas viram documento próprio e tabelas saem como tabelas Markdown.

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

- Reconhecer imagens que formam sequência (conversa, tutorial em telas, slides fotografados) e produzir um `.md` único por grupo (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Tratar imagem isolada como documento próprio; sequências são apenas um caso possível (esclarecimento do usuário, 2026-10-09).
- Montar tabelas como tabelas Markdown.

## Regras de negócio

- Briefing: o cliente isola a sequência em pasta própria, com nomes já em ordem sequencial; ordem por nome + EXIF + confirmação manual.
- Confirmação manual da ordem das imagens quando houver incerteza; nunca reordenar silenciosamente.
- Reordenação totalmente automática fica fora da V1 do briefing.

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

- Dentro: detectar/agrupar sequências, ordenar com confirmação, montar tabelas.
- Fora: OCR/conversão em si (0039); limpeza (0041).

## Dúvidas, decisões e riscos

- CONTRADIÇÃO a resolver: o briefing diz que o cliente isola cada sequência numa pasta; a mensagem do usuário diz que recebe 10 a 20 prints com três conversas misturadas. O sistema deve separar conversas misturadas sozinho?
- Como detectar o limite entre duas sequências na mesma pasta.
- Marco ainda não decidido.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
