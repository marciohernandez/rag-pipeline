# Backlog: Fase 1: recebimento e processamento de documentos até Markdown

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0033 |
| Status | Promoted |
| Produto | RAG Pipeline SaaS |
| Épico | Fase 1 — Ingestão multi-formato (PROJECT.md) |
| Funcionalidade | Conversão de documentos originais em Markdown |
| Tipo | História |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-09-28 |
| Refinado em | 2026-09-28 |
| Spec promovida | specs/draft/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/spec.md |

## Ideia original

vamos trabalhar na fase um do sistema, recebimento dos documentos e todo o processamento, extração das informações até o momento de colocar em arquivo .md para estarem prontos para seguir a fase 2

## Problema percebido

Hoje o único ponto de entrada de conteúdo é POST /api/v1/bases, que exige arquivos .md já prontos (rejeita qualquer extensão diferente de .md e exige UTF-8 válido). Não existe nenhuma etapa que receba um documento original (PDF, DOCX, imagem, etc.), extraia seu conteúdo e produza o Markdown que hoje precisa ser preparado manualmente antes do upload.

## Pessoa afetada ou beneficiada

Marcio e a equipe de consultoria, que hoje preparam manualmente o .md antes de criar uma Base; passariam a poder enviar o documento original diretamente.

## Resultado ou valor esperado

Uma pessoa envia um documento original e recebe automaticamente um Markdown estruturado, pronto para seguir para a Fase 2 (chunking/embeddings/Qdrant) e para o fluxo de Base já existente.

## Contexto

Este item abre a Fase 1 declarada em PROJECT.md (ingestão multi-formato, extração, curadoria e geração de Markdown), hoje não implementada: o loader (src/pipeline/loader.py) só lê .md já existentes em uma pasta local, e o upload de Base (src/app/routers/bases.py::enviar_base) só aceita .md. PROJECT.md também contém uma seção de limites desatualizada que ainda declara a ingestão multi-formato como 'prevista para o projeto-mãe' e fora de escopo — contradição a resolver quando o escopo deste item for confirmado.

## Referências relacionadas

- `specs/inbox/2026-09-28-141836-fase-1-recebimento-e-processamento-de-documentos-ate-markdown.md`: captura de origem deste item. Tipo: proveniência.
- `src/pipeline/loader.py`: loader atual, que só lê arquivos `.md` já existentes em uma pasta local — evidência do comportamento hoje ausente. Tipo: documentação relacionada.
- `src/app/routers/bases.py::enviar_base`: upload de Base atual, que só aceita `.md` (rejeita outras extensões, exige UTF-8, limita 5 MB/arquivo, 50 MB total, 50 arquivos) — permanece sem alteração nesta entrega, conforme decisão de desacoplamento abaixo. Tipo: documentação relacionada.
- `src/app/tasks.py` (`process_base_task`, Procrastinate): padrão de execução assíncrona já existente, reaproveitado pela decisão de processar em segundo plano. Tipo: documentação relacionada.
- `specs/backlog/0011-contrato-handoff-projeto-mae.md` e `specs/completed/0008-fronteira-interna-pipeline-aplicacao/spec.md` (SPEC-0008): estabelecem `src/pipeline/` como fachada de casos de uso consumida por `src/app/`, sem import direto de módulo interno — este item deve seguir o mesmo contrato de fronteira ao adicionar a extração multi-formato. Tipo: spec relacionada.
- `PROJECT.md`: declara a Fase 1 na visão consolidada (linhas 5-7), mas a seção de limites (linha 120-121) ainda afirma que a ingestão multi-formato está "prevista para o projeto-mãe" e fora de escopo — contradição a corrigir quando este item avançar. Tipo: documentação relacionada.
- `.specsfy/DATABASE.md`: registra o lote de conversão confirmado nesta descoberta (retenção de 7 dias, escopo por Workspace). Tipo: documentação relacionada.

## Comportamento esperado

- Na tela de detalhe do Workspace (`/workspaces/[id]`), uma seção/aba separada da criação de Base permite enviar um ou mais documentos originais (PDF, PPT, DOC/DOCX, XLS/XLSX, imagens JPG/PNG e formatos equivalentes), pelo mesmo padrão de painel lateral (Sheet) já usado por `UploadBaseSheet`.
- O envio cria um lote de conversão, processado em segundo plano (reaproveitando o padrão assíncrono de execução já existente via Procrastinate), sem bloquear a pessoa na requisição.
- Enquanto o lote processa, a pessoa acompanha a situação de cada documento (na fila, processando, concluído, falhou) no mesmo painel.
- Cada documento é extraído e convertido para Markdown preservando a estrutura original quando o formato permitir: títulos viram cabeçalhos, tabelas (PDF, DOCX, XLS) viram tabelas Markdown, cada slide de PPT vira uma seção, texto de imagem é extraído por OCR.
- Um documento que falha na extração não cancela os demais do lote: os que derem certo seguem para conclusão: os que falharem ficam listados com o motivo do erro, e a pessoa pode reenviar aquele arquivo específico ou seguir sem ele.
- Ao concluir, a pessoa baixa cada `.md` gerado individualmente ou baixa todos de uma vez em um pacote único.
- Este fluxo é independente da criação de Base: não cria, não altera nem depende de nenhuma Base. A pessoa decide depois, manualmente, quais `.md` (gerados aqui, só parte deles, ou outros quaisquer) enviar pelo fluxo de Base já existente, sem nenhuma mudança em `POST /api/v1/bases`. Unificar os dois fluxos num processo único é direção futura, fora de escopo desta entrega.
- Documento original e `.md` gerado ficam disponíveis por 7 dias após o processamento daquele documento terminar (sucesso ou falha definitiva) e depois são apagados automaticamente; o registro do lote (quais arquivos, o que deu certo ou falhou) permanece para histórico mesmo após os arquivos serem apagados.

## Regras de negócio

- Formatos aceitos nesta entrega: PDF, PPT, DOC/DOCX, XLS/XLSX e imagens (JPG/PNG e equivalentes via OCR). Qualquer outra extensão é rejeitada antes do processamento, com mensagem explícita.
- O upload de Base (`POST /api/v1/bases`, `.md` apenas) não muda nesta entrega; os dois fluxos não têm dependência entre si.
- Extração e conversão seguem a fronteira já estabelecida pela SPEC-0008: a nova capacidade vive em `src/pipeline/` (ou módulo equivalente exposto pela fachada de casos de uso) e `src/app/` a consome apenas por essa fachada, sem importar módulo interno.
- Mesma permissão de quem hoje pode criar uma Base no Workspace (papel com permissão de escrita) controla quem pode enviar documentos para conversão; visibilidade do lote segue o mesmo escopo de Workspace já usado por Base.
- Limite por arquivo aumenta em relação aos 5 MB atuais de Base (valor exato a confirmar na especificação, ex.: 40 MB); total do envio permanece 50 MB e quantidade permanece 50 arquivos por lote.

## Critérios de aceitação

```gherkin
Cenário: Converter documentos de formatos variados com sucesso
  Dado que a pessoa está na tela do Workspace com permissão de escrita
  Quando ela envia um PDF, uma planilha XLS e uma imagem JPG pelo painel de conversão
  Então o lote é processado em segundo plano
  E cada documento aparece com sua situação (na fila, processando, concluído)
  E ao concluir, a pessoa baixa o .md de cada um individualmente ou baixa todos em um pacote único
  E nenhuma Base é criada ou alterada por esse envio

Cenário: Um documento falha sem derrubar o lote inteiro
  Dado um lote com três documentos, um deles um PDF corrompido
  Quando o processamento termina
  Então os dois documentos válidos aparecem concluídos com seus .md disponíveis para download
  E o documento corrompido aparece como falhou, com o motivo do erro
  E a pessoa pode reenviar apenas esse arquivo ou seguir sem ele

Cenário: Preservar estrutura na conversão
  Dado um DOCX com títulos e uma tabela
  Quando o documento é convertido
  Então o .md gerado usa cabeçalhos Markdown para os títulos
  E a tabela do DOCX vira uma tabela Markdown equivalente

Cenário: Rejeitar formato não suportado
  Dado um arquivo .zip enviado ao painel de conversão
  Quando a pessoa tenta enviar esse arquivo
  Então o sistema recusa o arquivo antes de iniciar o processamento
  E informa que a extensão não é suportada

Cenário: Apagar arquivos após o prazo de retenção
  Dado um documento processado com sucesso há mais de 7 dias
  Quando o prazo de retenção expira
  Então o documento original e o .md gerado são apagados automaticamente
  E o registro do lote continua mostrando quais arquivos existiram e seu resultado
```

## Qualidades e operação

- Segurança: mesma permissão de escrita já usada para criar Base; nenhum documento ou .md fica acessível fora do escopo do Workspace/tenant/projeto de quem enviou.
- Privacidade: conteúdo dos documentos enviados pode ser sensível (material de consultoria); apagamento automático em 7 dias reduz a janela de exposição. Nenhum dado é compartilhado com terceiros além do processamento de extração/OCR local.
- Desempenho e volume: processamento assíncrono evita timeout de requisição HTTP em lotes grandes ou com OCR lento; limite por arquivo, total e quantidade a confirmar na especificação técnica.
- Auditoria e observabilidade: situação de cada documento (fila, processando, concluído, falhou) e o motivo de cada falha ficam visíveis à pessoa; o registro do lote sobrevive à expiração dos arquivos.

## Dependências

- SPEC-0008 (concluída), fronteira `src/pipeline/`/`src/app/`: a nova extração deve respeitar a fachada de casos de uso já estabelecida.
- Nenhuma dependência bloqueante identificada (diferente do padrão do BACKLOG-0011/0012/0013, que tratava dívidas técnicas anteriores).

## Situações de erro

- Documento com extensão não suportada: recusado antes do processamento, com mensagem explícita.
- Documento corrompido ou ilegível (ex.: PDF corrompido, imagem sem texto reconhecível por OCR): marcado como falhou, com o motivo, sem afetar os demais do lote.
- Arquivo acima do limite por documento ou lote acima do limite total/quantidade: recusado no envio, mesmo padrão de mensagem já usado por Base hoje.
- Expiração do prazo de retenção antes do download: os arquivos somem; a pessoa precisa reenviar o documento original para gerar um novo .md.

## Escopo

- Dentro: painel de envio na tela de Workspace; processamento assíncrono com acompanhamento de situação por documento; extração com preservação de estrutura para PDF, PPT, DOC/DOCX, XLS/XLSX e imagens (OCR); tratamento de falha parcial por documento; download individual e em pacote; retenção de 7 dias com apagamento automático; registro do lote em `.specsfy/DATABASE.md`.
- Fora: qualquer alteração em `POST /api/v1/bases` ou no fluxo de criar Base; unificação dos dois fluxos num processo único (direção futura); revisão ou edição do `.md` dentro do sistema antes do download; curadoria cruzada, detecção de contradições ou loop de feedback humano (já fora de escopo declarado em PROJECT.md); correção da contradição de PROJECT.md sobre escopo do projeto-mãe (registrar como ajuste documental separado, não requisito funcional).

## Dúvidas, decisões e riscos

- Decisão confirmada (Pergunta 1 do refinamento): a conversão de documentos é uma funcionalidade independente da criação de Base nesta entrega; unificar os dois é direção futura explícita, não requisito agora.
- Decisão confirmada (Pergunta 2): formatos aceitos são PDF, PPT, DOC/DOCX, XLS/XLSX e imagens via OCR — escolha da pessoa, mais amplo que a recomendação inicial de só PDF/DOCX.
- Decisão confirmada (Pergunta 3): o Markdown gerado preserva estrutura (títulos, tabelas, slides como seções) quando o formato permitir.
- Decisão confirmada (Pergunta 4): limite por arquivo aumenta; total (50 MB) e quantidade (50 arquivos) do envio permanecem os mesmos de Base hoje. Valor exato do novo limite por arquivo fica para a especificação técnica (suposição reversível).
- Decisão confirmada (Pergunta 5): falha em um documento não cancela o lote; documentos com sucesso seguem, falhas são reportadas com opção de reenviar ou continuar sem eles.
- Decisão confirmada (Pergunta 6): sem revisão/edição dentro do sistema; a pessoa baixa, analisa fora da ferramenta, e decide depois o que sobe manualmente no fluxo de Base já existente.
- Decisão confirmada (Pergunta 7): processamento em segundo plano, reaproveitando o padrão assíncrono já existente (Procrastinate/execuções).
- Decisão confirmada (Interface, Pergunta 1): a tela vive em `/workspaces/[id]`, como seção/aba separada da criação de Base.
- Decisão confirmada (Interface, Pergunta 2): composição em painel lateral (Sheet), consistente com `UploadBaseSheet`.
- Decisão confirmada (Interface, Pergunta 3): download por lista individual por arquivo + botão "baixar todos".
- Decisão confirmada (via `$specsfy-data-discovery`): documento original e `.md` gerado são apagados automaticamente 7 dias após o processamento daquele documento terminar; o registro do lote permanece para histórico. Detalhes completos em `.specsfy/DATABASE.md`.
- Risco registrado: `PROJECT.md` ainda declara em sua seção de limites que a ingestão multi-formato está "prevista para o projeto-mãe" e fora de escopo — texto desatualizado frente à consolidação já registrada no topo do mesmo arquivo. Precisa ser corrigido quando este item avançar (ajuste documental, não requisito funcional novo).
- Risco registrado: OCR de imagens é inerentemente mais lento e menos preciso que extração de texto nativo; qualidade esperada e idioma do OCR ainda não foram detalhados — ficam para a especificação técnica como suposição reversível (idioma português como padrão, melhor esforço sem bloqueio por baixa confiança).
- Nenhuma lacuna material bloqueante permanece neste item; itens acima marcados como "suposição reversível" podem amadurecer durante a especificação sem exigir nova rodada de perguntas.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Brief pronto para especificar

1. **Problema e objetivo:** não existe nenhuma etapa que receba um documento original (PDF, PPT, DOC/DOCX, XLS/XLSX, imagem) e o converta em Markdown; hoje só `.md` já pronto é aceito, tanto pelo loader do pipeline quanto pelo upload de Base.
2. **Atores:** Marcio e a equipe de consultoria, com permissão de escrita no Workspace.
3. **Escopo:** painel de envio na tela de Workspace (seção separada da criação de Base); processamento assíncrono com situação por documento; extração com preservação de estrutura; falha parcial não bloqueia o lote; download individual e em pacote; retenção de 7 dias.
4. **Fora de escopo:** qualquer mudança em `POST /api/v1/bases`; unificação futura dos dois fluxos; revisão/edição do `.md` dentro do sistema; curadoria cruzada e detecção de contradições.
5. **Jornadas e regras essenciais:** enviar documentos → acompanhar processamento em segundo plano → baixar `.md` gerados (individual ou em pacote) → decidir manualmente, fora deste fluxo, o que sobe como Base.
6. **Aceite:** cinco cenários Given/When/Then cobrindo conversão multi-formato bem-sucedida, falha parcial sem cancelar o lote, preservação de estrutura, rejeição de formato não suportado e apagamento automático após 7 dias.
7. **Restrições:** fachada `src/pipeline/` consumida apenas por `src/app/` (SPEC-0008); mesma permissão de escrita de Base; limite por arquivo maior que os 5 MB atuais, total e quantidade inalterados.
8. **Suposições confirmadas:** valor exato do novo limite por arquivo, idioma/qualidade esperada do OCR, e a forma exata de manter o registro do lote após a expiração dos arquivos ficam como defaults reversíveis para a especificação técnica.
9. **Decisões abertas:** nenhuma decisão material bloqueante. A correção da seção de limites desatualizada em `PROJECT.md` é um ajuste documental a registrar junto da especificação, não uma decisão de produto pendente.

## Próximo passo

Pronto para `$specsfy-03-specify`.
