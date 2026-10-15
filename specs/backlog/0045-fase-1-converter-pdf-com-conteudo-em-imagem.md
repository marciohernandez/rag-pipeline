# Backlog: Fase 1: converter PDF cujo conteúdo está em imagem (OCR em páginas de PDF)

| Metainformação | Valor |
| --- | --- |
| ID | BACKLOG-0045 |
| Status | Promoted |
| Produto | rag-pipeline |
| Épico | Fase 1: recebimento e processamento até Markdown |
| Funcionalidade | Conversão de documentos (PDF) |
| Tipo | Melhoria |
| Prioridade | Não priorizado |
| Milestones | |
| Criado em | 2026-10-14 |
| Spec promovida | specs/planned/0033-fase-1-converter-pdf-com-conteudo-em-imagem/spec.md |

## Ideia original

O conversor de PDF só lê a camada de texto. Um PDF de página web impressa gerou um .md só com o parágrafo do topo, perdendo o resto, que é imagem dentro do PDF. A pessoa disse que receber documentos assim é muito comum e que isso deve estar previsto e funcionando.

## Problema percebido

PDFs com conteúdo em imagem saem quase vazios do conversor (pymupdf4llm só lê texto); o FR-003 da SPEC-0023 prevê OCR apenas para arquivos de imagem.

## Pessoa afetada ou beneficiada

Pessoa que prepara documentos para a base vetorial (equipe de consultoria que usa o sistema).

## Resultado ou valor esperado

PDF com páginas em imagem gera .md com o texto reconhecido por OCR, e o relatório do lote sinaliza a qualidade.

## Contexto

Fase 1, depois da SPEC-0023. Tesseract e pytesseract já existem; o OCR hoje só roda em JPG/PNG. Captura: specs/inbox/2026-10-14-125322-converter-pdf-cujo-conteudo-esta-em-imagem-ocr-em-paginas-de-pdf.md

## Referências relacionadas

- `specs/inbox/2026-10-14-125322-converter-pdf-cujo-conteudo-esta-em-imagem-ocr-em-paginas-de-pdf.md` — captura de origem (recriada da memória).
- `specs/completed/0023-fase-1-recebimento-e-processamento-de-documentos-ate-markdown/spec.md` — spec relacionada; o FR-003 limita o OCR a arquivos de imagem.
- `specs/backlog/0039-fase-1-receber-e-converter-formatos.md` — backlog relacionado; a detecção de PDF só de imagem foi movida para este item (decisão do usuário, Pergunta 1, opção 3).
- `src/pipeline/conversion/converters/pdf.py` e `image.py` — código atual (fato).

## Comportamento esperado

Ao converter um PDF, o sistema identifica cada página sem texto útil (declaração do usuário na Pergunta 2, opção 1) e aplica OCR só nelas. As páginas com texto continuam no `pymupdf4llm`. O `.md` final junta, na ordem das páginas, o texto nativo e o texto reconhecido.

## Regras de negócio

- OCR por página, apenas onde não há texto útil ou ele é muito curto para a página (Pergunta 2, opção 1).
- Limite de páginas com OCR por documento, configurável (Pergunta 4, opção 1). Passando dele, as páginas restantes não são lidas e o documento fica "revisar" com o motivo.
- O documento fica "revisar" no relatório do lote quando o OCR devolve pouco texto ou baixa confiança do Tesseract; OCR com boa leitura não gera aviso (Pergunta 3, opção 3).
- Idioma do OCR configurável, padrão `por+eng`, valendo também para o OCR de imagem (Pergunta 5, opção 3). Mudança em comportamento já entregue; reversível pela configuração.
- Valores configurados no `config.yaml`, numa seção de conversão (Pergunta 6, opção 3).

## Critérios de aceitação

- Dado um PDF com parágrafo de texto no topo e o restante como imagem, quando for convertido, então o `.md` contém o texto do topo e o texto reconhecido por OCR das demais páginas.
- Dado um PDF só de texto, quando for convertido, então o OCR não roda e o resultado é igual ao de hoje.
- Dado um PDF com mais páginas em imagem que o limite configurado, quando for convertido, então só as páginas até o limite passam por OCR e o documento fica "revisar" com o motivo no relatório do lote.
- Dado um OCR com pouco texto ou baixa confiança, quando o lote terminar, então o documento aparece como "revisar" e a lista indica as páginas lidas por OCR.
- Dado `idioma` alterado no `config.yaml`, quando uma imagem ou um PDF for convertido, então o OCR usa o novo valor.

## Qualidades e operação

- Segurança: OCR local (Tesseract); nada é enviado a serviço externo.
- Privacidade: PDFs reais trazem dados pessoais; o PDF de exemplo não pode ser versionado nem usado como fixture. Os testes usam PDF sintético gerado no teste.
- Desempenho e volume: o OCR é lento; o processamento segue assíncrono (NFR-001 da SPEC-0023) e o limite de páginas protege o worker.
- Auditoria e observabilidade: o relatório do lote registra páginas lidas por OCR, confiança baixa e limite atingido.

## Dependências

- SPEC-0023 (concluída): conversores e relatório do lote.
- Tesseract com os idiomas `por` e `eng` no ambiente do worker, local e em produção (a conferir na imagem da stack de produção, backlog 0028).

## Situações de erro

- Tesseract ausente ou falha no OCR de uma página: o documento fica "revisar" com o motivo, sem derrubar o lote; as outras páginas seguem.
- PDF protegido ou corrompido: mantém o comportamento atual de falha na conversão.

## Escopo

- Dentro: detecção de página sem texto útil, OCR por página, sinal "revisar", limite de páginas, idioma configurável, seção de conversão no `config.yaml`.
- Fora: tela de configurações da conversão (item futuro, decisão da Pergunta 6); reprocessar com IA e outros formatos (backlog 0039); reagrupar sequências (0040).

## Dúvidas, decisões e riscos

- Decisão (2026-10-14): item separado do 0039, que cedeu a detecção de PDF só de imagem (Pergunta 1, opção 3).
- Pergunta 6, opção 2 (tela da SPEC-0029): descartada como não aplicável, pois a 0029 trata só de chunking; resposta final: opção 3.
- Pergunta 7, opção 1: o sinal "Revisar" é entregue completo (coluna `avisos` com migration, campo na API e selo na lista), pois os avisos de conversão eram descartados.
- Área de perguntas fechada em 7 de 8 perguntas, com o brief suficiente.
- Em aberto, para a spec: valor padrão do limite de páginas (sugestão 50), limiares numéricos de "pouco texto" e "baixa confiança", e se a imagem de produção já tem Tesseract.
- Risco: alterar o idioma padrão do OCR de imagem de `por` para `por+eng` muda resultados já entregues.

## Pronto para desenvolvimento

- [x] O problema e a pessoa beneficiada estão claros.
- [x] O evento inicial e o resultado esperado estão claros.
- [x] Permissões, regras e exceções relevantes estão claras.
- [x] O resultado pode ser verificado objetivamente.
- [x] Segurança, privacidade e desempenho foram avaliados conforme o risco.
- [x] Fora de escopo, dependências e decisões pendentes estão registrados.

## Próximo passo

Seguir para `$specsfy-03-specify`.
