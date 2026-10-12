# Backlog: Fase 1: receber e converter documentos de vários formatos para Markdown

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0039 |
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

receber os arquivos em docs, html, pdf, ppt, imagens, planilhas e url e extrair as informações; usar OCR e bibliotecas conhecidas primeiro e LLM por último (capturas de 2026-10-09)

## Problema percebido

O sistema só aceita .md; documentos reais chegam em PDF, Office, Google, imagens e URL e não entram no pipeline.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Qualquer formato previsto vira texto/Markdown bruto rastreável ao arquivo de origem, usando bibliotecas e OCR antes de LLM.

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

- Aceitar PDF nativo, PDF vetorizado/visual, Word, Excel, PPTX nativo, Google Slides/Docs/Planilhas **exportados** (PPTX, DOCX, XLSX), imagem solta (JPG, PNG), sequência de imagens e URL (declaração do usuário; briefing.md do projeto-mãe v. 2026-07-29, colado na conversa de 2026-10-09).
- Escolher a estratégia de extração pelo conteúdo real do arquivo, não pela extensão; ordem: bibliotecas e OCR primeiro, LLM por último (declaração do usuário, 2026-10-09).
- Gerar um `.md` por documento, ou por grupo de imagens complementares.

## Regras de negócio

- Google chega já exportado; o sistema não acessa a API do Google (decisão da Pergunta 2, resolvida pelo briefing).
- 1 URL = 1 documento; sem crawling de links internos; só a URL explicitamente enviada.
- Excel: a escolha das abas a processar exige confirmação manual.

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

- Dentro: conversão de todos os formatos acima em Markdown bruto rastreável à origem.
- Fora: reagrupamento de sequências (0040); filtro de domínio e limpeza (0041); contradições (0042, 0043); crawling; acesso à API do Google.

## Dúvidas, decisões e riscos

- Como o envio recebe os formatos novos (interface atual só aceita `.md`; SPEC-0030).
- Limites de tamanho e de páginas por arquivo.
- Onde roda a conversão: antes do envio ou no worker.
- Marco de roadmap ainda não decidido (M01 e M02 fechados; M03 é deploy).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Aprofundar nesta etapa até o item ficar pronto para `$specsfy-03-specify`.
