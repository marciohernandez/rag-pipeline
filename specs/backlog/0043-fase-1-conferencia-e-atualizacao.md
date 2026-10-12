# Backlog: Fase 1: registrar a decisão da empresa e atualizar os Markdown para a Fase 2

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0043 |
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

após conferir com a empresa o que está valendo, atualizar os .md e deixá-los prontos para a segunda parte (mensagens de 2026-10-09)

## Problema percebido

Sem um passo que traga a decisão da empresa de volta, os .md continuam contraditórios e a Fase 2 indexaria informação não validada.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

A decisão sobre cada contradição é registrada e os .md são atualizados, liberando a entrega à Fase 2.

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

- O relatório vai à empresa (dona da informação), que responde em formato livre; um agente de IA interpreta e mapeia a resposta às contradições (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Nenhuma correção é gravada sem confirmação humana explícita da consultoria.
- Aplicar a correção confirmada, rodar nova análise e repetir até não haver contradições.

## Regras de negócio

- Checkpoint humano obrigatório antes de qualquer escrita no `.md`.
- A conferência com a empresa acontece fora do sistema.

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

- Dentro: registro da decisão, confirmação humana, aplicação da correção e novo ciclo.
- Fora: a detecção em si (0042).

## Dúvidas, decisões e riscos

- Como a resposta da empresa entra no sistema (colada, anexo).
- Versionamento dos `.md` e histórico das decisões.
- Meta do briefing: ≥70% dos `.md` finais validados sem correção manual após o primeiro ciclo.

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
