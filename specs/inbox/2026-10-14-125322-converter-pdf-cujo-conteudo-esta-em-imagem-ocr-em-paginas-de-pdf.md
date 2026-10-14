# Inbox: Converter PDF cujo conteúdo está em imagem (OCR em páginas de PDF)

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-14T12:53:22Z |
| Slug | converter-pdf-cujo-conteudo-esta-em-imagem-ocr-em-paginas-de-pdf |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `01639933ea8248d25c571bedc0094c1b1b8b76b612de7bed0f84792c51f40119` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

é muito importante que isso esteja anotado para não esquecer. é muito comum receber documentos dessa forma e isso deve estar previsto e funcionando

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** PDFs que são páginas impressas ou capturas, com o conteúdo em imagem e só um trecho de texto selecionável, hoje saem do conversor quase vazios; a pessoa quer que esse caso esteja previsto e funcionando.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** Teste manual na aba Conversão de documentos (2026-10-14): um PDF de página web impressa (confirmação de pedido de um serviço) teve só o parágrafo do topo, que é texto real, no .md gerado; o restante da página (títulos, passos, telefones, número do pedido, endereço, plano e pagamento) é imagem dentro do PDF e foi perdido. O conversor de PDF atual extrai apenas a camada de texto e não faz OCR em imagens embutidas.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Marcio e a equipe de consultoria, que recebem documentos nesse formato com frequência (declarado: 'é muito comum receber documentos dessa forma').

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Todo documento recebido nesse formato produz um Markdown completo, sem perda silenciosa de conteúdo.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: o caso é comum e deve estar previsto e funcionando. Inferência: a solução provável é renderizar as páginas com pouco texto ou com imagem relevante e passá-las por OCR, juntando o resultado ao texto já extraído; hoje o FR-003 da SPEC-0023 só prevê OCR para arquivos de imagem (JPG/PNG). Inferência: o conversor deveria sinalizar quando um PDF sai com muito menos conteúdo do que a página tem, para a pessoa não confiar num .md incompleto.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Dependência do Tesseract e do pacote de idioma português, que não estão instalados no ambiente local de desenvolvimento (a SPEC-0023 já os prevê na imagem de produção). OCR é mais lento e menos preciso que texto nativo. Risco de duplicar conteúdo quando a página tem texto e imagem sobrepostos. O PDF de exemplo contém dados pessoais e não deve ser versionado nem copiado para fixtures.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Spec nova ou revisão da SPEC-0023 com requisito de PDF com páginas em imagem; critério de decisão por página (pouco texto ou imagem grande) a definir no refinamento; aviso ao usuário quando a extração parecer incompleta; fixture sintética, sem dados reais, para o teste.

## Pontos a revisar no futuro

**A revisar:** Como decidir quais páginas passam por OCR; se o aviso de extração incompleta entra na mesma entrega; idioma(s) do OCR; limite de tempo e de páginas por documento; instalar Tesseract no ambiente local; destino do PDF de exemplo (contém dados pessoais) para teste.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
