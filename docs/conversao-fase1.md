# Conversão de documentos: HTML, páginas, abas e leitura com IA

A tela existente de conversão do Workspace recebe arquivos e endereços públicos.
O resultado continua sendo um Markdown por documento, independente das coleções.

## Fluxo de uso

1. Abra **Converter documentos** no Workspace. Em **Arquivos**, escolha os originais, incluindo `.html`; em **Endereço**, adicione uma ou mais páginas públicas.
2. Confira os limites exibidos, obtidos da API. A API preserva documentos que cabem no teto e devolve nome e motivo de cada recusa.
3. Uma planilha com várias abas aguarda seleção, inicialmente com todas marcadas. Escolha ao menos uma e confirme. Planilhas de uma aba seguem diretamente para a fila.
4. Acompanhe o lote e baixe o Markdown. O selo **Revisar** indica sinais de leitura ruim, sem chamada automática a IA.
5. Owner/admin podem abrir **Reprocessar com IA** no documento concluído. O diálogo informa o envio ao provedor; cancelar não envia conteúdo. Em sucesso, o Markdown é substituído; em falha, permanece intacto e uma mensagem segura aparece.

Member consulta e baixa; não confirma abas nem solicita IA. Os controles usam
teclado, rótulos e alertas associados. As composições estão em `INTERFACE.md`.

## API e processamento

| Endpoint | Contrato |
| --- | --- |
| `GET /api/v1/conversoes/limites` | Tetos de arquivo, lote e quantidade, sem configuração secreta |
| `POST /api/v1/conversoes` | Multipart com `workspace_id`, `arquivos` e/ou lista `urls`; 201 com documentos aceitos e `recusados`; 400 se nenhum puder ser aceito |
| `POST /api/v1/conversoes/{lote}/documentos/{doc}/abas` | JSON `abas`; 200 enfileira, 400 seleção inválida/expirada, 409 confirmação repetida |
| `POST /api/v1/conversoes/{lote}/documentos/{doc}/reprocessar-ia` | 202 enfileira após permissão; 403 para leitura, 409 se indisponível |

O worker busca só a página informada, sem seguir links do HTML. A conexão usa o
IP validado, preserva Host/SNI e verifica o certificado TLS. Cada redirecionamento
é validado novamente; endereços privados, locais, reservados e respostas DNS
mistas são recusados. Scripts, estilos e recursos externos não são executados.

O original da URL preserva os parâmetros necessários à busca no storage sujeito
à retenção. Metadados, Markdown de origem e mensagens não expõem query string.
O teto acumulado considera o corpo recebido, com reserva serializada por lote.

## Configuração e execução

Os valores são injetados pelo entrypoint na seção `conversao` do YAML:

| Campo | Padrão |
| --- | --- |
| `max_arquivos` | 50 |
| `max_bytes_arquivo` | 40 MiB |
| `max_bytes_lote` | 50 MiB |
| `timeout_url_s` | 10 segundos |
| `max_bytes_url` | 5 MiB |
| `max_redirecionamentos` | 5 |
| `minimo_texto_util` | 40 caracteres |
| `max_proporcao_substituicao` | 0,05 |

A IA usa a configuração `llm` existente e recebe páginas/imagens por mensagens
neutras. PDFs e imagens são renderizados por PyMuPDF; Office usa LibreOffice,
já presente na imagem do backend. Ausência local do renderer, modelo sem visão
ou falha de provedor gera erro seguro. Nenhum job normal chama o modelo; jobs
repetidos sem nova solicitação não reprocessam um documento já concluído.

A revisão Alembic `0036_conversao_formatos` adiciona apenas campos opcionais.
A retenção de sete dias permanece para os arquivos, inclusive durante a espera
pela seleção de abas. Os registros de histórico continuam preservados.

## Verificação

Pytest cobre rede simulada, transporte com IP fixo, worker, isolamento, migração,
limites e IA sem provedor real. Vitest cobre a entrada por teclado, seleção vazia
e confirmação/cancelamento/falha da IA. Chromium verifica a interface em 375 px,
desktop e zoom; detalhes e evidências ficam na spec canônica da SPEC-0036.
