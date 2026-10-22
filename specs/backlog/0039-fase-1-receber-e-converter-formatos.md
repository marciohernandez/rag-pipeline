# Backlog: Fase 1: receber e converter documentos de vários formatos para Markdown

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0039 |
| Status | Promoted |
| Produto | A esclarecer |
| Épico | A esclarecer |
| Funcionalidade | A esclarecer |
| Tipo | A esclarecer |
| Prioridade | Não priorizado |
| Milestones | M04 |
| Criado em | 2026-10-09 |
| Spec promovida | specs/completed/0036-fase-1-receber-e-converter-formatos/spec.md (SPEC-0036) |

## Ideia original

receber os arquivos em docs, html, pdf, ppt, imagens, planilhas e url e extrair as informações; usar OCR e bibliotecas conhecidas primeiro e LLM por último (capturas de 2026-10-09)

## Problema percebido

O sistema só aceita .md; documentos reais chegam em PDF, Office, Google, imagens e URL e não entram no pipeline.

## Pessoa afetada ou beneficiada

Pessoa da consultoria que prepara a base de conhecimento a partir de documentos recebidos de empresas clientes

## Resultado ou valor esperado

Qualquer formato previsto vira texto/Markdown bruto rastreável ao arquivo de origem, usando bibliotecas e OCR antes de LLM.

## Contexto

Fase 1 do rag-pipeline (PROJECT.md:6). Atualização de 2026-10-13: a SPEC-0023 (mergeada na `main`, #22) já converte PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX e imagem (OCR) em `.md`, com processamento assíncrono, download individual ou em pacote e retenção de 7 dias (`src/pipeline/conversion/converters/{docx,image,pdf,pptx,xlsx}.py`, `legacy_office.py`, `factory.py`). Este item cobre só o que a 0023 não entrega: HTML e URL, escolha da estratégia pelo conteúdo, escolha de abas do Excel, limites e reprocessamento com IA. Google exportado já é coberto (chega como DOCX, PPTX ou XLSX). Capturas: specs/inbox/2026-10-09-192547-*.md e 2026-10-09-194532-*.md. Entradas variam: PDF (inclusive prints de PPT/PPTX e fotos), Google Docs/Planilhas, XLS, imagens JPG/PNG (conversas, apresentações, telas de app; podem ou não ser sequência), URLs. Áreas: comercial, atendimento, RH, marketing, diretoria. Saída: .md limpos, sem contradições nem duplicidade, prontos para a Fase 2. Contrato do .md: SPEC-0002. Dividido em 5 backlogs por decisão do usuário em 2026-10-09 (Pergunta 1, opção 1).

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
- **HTML e URL (decisão da Pergunta 2, 2026-10-13, opção 3):** a pessoa pode colar um endereço (URL) na tela de Conversão ou enviar um arquivo `.html` salvo; os dois geram um `.md` por página.
- **Páginas que dependem de scripts (Pergunta 3, opção 3):** nesta entrega só páginas com o texto já no HTML. Se a página vier vazia, o sistema avisa "não consegui extrair o conteúdo" e sugere salvar o `.html` pelo navegador e enviá-lo. Navegador automático fica como evolução futura, fora desta entrega.
- **Excel (Pergunta 6, opção 1):** antes de converter, o sistema mostra as abas, todas marcadas; a pessoa desmarca as que não servem e confirma; só as marcadas viram `.md`.
- **IA (Pergunta 7, opção 3):** a conversão usa bibliotecas e OCR. Documento com leitura de baixa qualidade fica marcado "revisar" no relatório do lote; a IA só roda quando a pessoa pedir, documento a documento, por um botão de reprocessar com IA. Nada é enviado a serviço externo sem esse pedido.

## Regras de negócio

- **Endereços permitidos (Pergunta 4, opção 1):** qualquer endereço público `http` ou `https`; endereços da rede interna e da própria máquina são bloqueados automaticamente (proteção contra o servidor ser usado para ler a rede interna).
- **Limites (Pergunta 5, opção 2):** teto por arquivo ou página e teto para o total do envio; valores exatos por configuração (referência de partida: 50 MB por arquivo e 500 MB por lote, não confirmados). Acima do teto, só aquele documento é recusado, com mensagem clara, e os demais seguem.

- Google chega já exportado; o sistema não acessa a API do Google (decisão da Pergunta 2, resolvida pelo briefing).
- 1 URL = 1 documento; sem crawling de links internos; só a URL explicitamente enviada.
- Excel: a escolha das abas a processar exige confirmação manual.

## Critérios de aceitação

Derivados das decisões confirmadas (Perguntas 2 a 7); valores marcados como "a definir" seguem abertos.

- Dado um endereço público `http` ou `https` com o texto no HTML, quando a pessoa o cola na tela de Conversão, então é gerado um `.md` rastreável à URL de origem.
- Dado um arquivo `.html` salvo, quando a pessoa o envia, então é gerado um `.md` para a página.
- Dado um endereço da rede interna ou da própria máquina (inclusive via redirecionamento), quando a pessoa o envia, então ele é recusado com mensagem clara e nada é buscado.
- Dado uma página cujo texto depende de scripts e chega vazia, quando convertida, então o sistema avisa "não consegui extrair o conteúdo" e sugere salvar o `.html` pelo navegador e enviá-lo.
- Dado um arquivo Excel com várias abas, quando enviado, então o sistema mostra as abas todas marcadas, e só as marcadas confirmadas viram `.md`.
- Dado um arquivo ou página acima do teto por arquivo, ou um envio acima do teto do lote, então só o documento excedente é recusado com mensagem clara e os demais seguem.
- Dado um documento com leitura de baixa qualidade, quando o lote termina, então ele aparece marcado "revisar" no relatório do lote, sem uso de IA.
- Dado um documento marcado "revisar", quando a pessoa aciona "reprocessar com IA", então só esse documento é enviado à IA; sem o clique, nada vai a serviço externo.
- Dado qualquer formato aceito, então a escolha da estratégia usa o conteúdo real do arquivo e tenta bibliotecas e OCR antes de LLM.

## Qualidades e operação

- Segurança (decisão, Pergunta 4): bloqueio de rede interna e da própria máquina, inclusive em redirecionamentos. Inferência a confirmar na spec: tempo limite, tamanho máximo da resposta e número máximo de redirecionamentos.
- Privacidade (decisão, Pergunta 7): nada é enviado a serviço externo sem o pedido explícito de reprocessar com IA, documento a documento.
- Desempenho e volume (decisão, Pergunta 5): tetos por arquivo e por lote, por configuração; referência de partida de 50 MB por arquivo e 500 MB por lote, não confirmada. Limite de páginas em aberto. Processamento assíncrono já existente (SPEC-0023).
- Auditoria e observabilidade: a definir na spec; o relatório do lote já registra "revisar" e as recusas por teto.

## Dependências

- SPEC-0023 (conversão existente), SPEC-0002 (contrato do `.md`), SPEC-0030 (envio por coleção).
- BACKLOG-0045 (PDF só de imagem) é independente.

## Situações de erro

- Endereço bloqueado, página vazia por scripts, resposta acima do teto, tempo esgotado e arquivo corrompido: mensagem clara por documento, sem derrubar o lote. Textos exatos a definir na spec.

## Escopo

- Dentro: conversão de todos os formatos acima em Markdown bruto rastreável à origem.
- Fora: reagrupamento de sequências (0040); filtro de domínio e limpeza (0041); contradições (0042, 0043); crawling; acesso à API do Google.

## Dúvidas, decisões e riscos

- Resolvido: o envio e a conversão já existem na aba "Conversão de documentos" (SPEC-0023), com processamento assíncrono; URL e `.html` entram nessa mesma tela.
- Resolvido (Pergunta 5): limites por arquivo e por lote, configuráveis. Em aberto: valores finais e limite de páginas.
- Resolvido (Pergunta 8, opção 1): a Fase 1 ganha um marco novo entre o M02 e o deploy (M03 continua sendo deploy). Falta criá-lo via `$specsfy-roadmap-milestone-interviewer`.
- Em aberto: o critério de "baixa qualidade" que marca "revisar" nos demais formatos.
- Movido em 2026-10-14: a detecção e o OCR de PDF só de imagem (PDF de texto vs PDF de imagem) passam a ser tratados em `specs/backlog/0045-fase-1-converter-pdf-com-conteudo-em-imagem.md`; este item não os especifica.
- Área de perguntas do 0039 encerrada no limite de oito perguntas (2026-10-13).
- Risco: segurança da busca de URL (bloqueio de rede interna, redirecionamentos para endereços internos, tamanho da resposta, tempo limite).

## Pronto para desenvolvimento

- [ ] O problema e a pessoa beneficiada estão claros.
- [ ] O evento inicial e o resultado esperado estão claros.
- [ ] Permissões, regras e exceções relevantes estão claras.
- [ ] O resultado pode ser verificado objetivamente.
- [ ] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [ ] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Promovido para a SPEC-0036 (Draft). Próximo: `$specsfy-04-validate`. Pendências levadas à spec como `Pendente`: valores finais dos tetos e limite de páginas; critério de "baixa qualidade"; limites da busca de URL (tempo, tamanho, redirecionamentos); criação do marco da Fase 1 via `$specsfy-roadmap-milestone-interviewer`.

## Entrega registrada — 2026-10-15

SPEC-0036 concluída com 43/43 tarefas, gates da fatia aprovados e evidências no diretório canônico acima. As decisões de refinamento e o histórico da promoção inicial são preservados.
