# Inbox: Enxugar o LibreOffice na imagem de produção (ou rever .doc/.ppt/.xls)

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-14T13:09:24Z |
| Slug | enxugar-o-libreoffice-na-imagem-de-producao-ou-rever-doc-ppt-xls |
| Origem | Input do usuário |
| Processamento | Análise inicial sem perguntas |
| Sessão de descoberta | Captura avulsa. |
| Turno da conversa | Não se aplica. |
| Integridade do original | SHA-256 `6a09bbf98471869ee0ab8fe2957bc45547415ad1afaff2efc3f9c6a54adc6ac4` |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

sim vamos seguir (em resposta a: registrar na Inbox a otimização dos pacotes do LibreOffice na imagem de produção, para não esquecer). Contexto da pergunta da pessoa: 'quando for colocar em produção vou precisar ter o libreoffice para documentos .doc, .xls, .ppt etc? não existem nenhuma biblioteca que faz essa leitura para a extração das informações em nosso sistema?'

## Contexto consultado

Nenhuma fonte contextual consultada.

## Resumo processado

**Inferência:** A conversão de .doc, .ppt e .xls depende do LibreOffice, que deixa a imagem de produção pesada; registrar a otimização dos pacotes e a decisão de produto sobre manter ou não os formatos antigos.

## Análise inicial

### Problema ou oportunidade

**Declaração ou inferência identificada:** A SPEC-0023 (DEC-006) normaliza .doc, .ppt e .xls com o LibreOffice headless antes da extração. Não há alternativa Python boa: .xls tem xlrd; .doc e .ppt só têm programas externos (antiword/catdoc ou Apache Tika) que perdem títulos e tabelas ou exigem Java. O LibreOffice completo passa de 1 GB na imagem.

### Pessoas afetadas ou beneficiadas

**Declaração ou inferência identificada:** Quem opera o deploy e quem envia documentos antigos (Marcio e a equipe de consultoria).

### Resultado ou valor esperado

**Declaração ou inferência identificada:** Imagem de produção menor e build mais rápido, sem perder a fidelidade de títulos e tabelas dos formatos antigos, ou uma decisão explícita de excluí-los.

### Sinais de escopo, regras ou solução

**Sinais extraídos, não decisões:** Declaração: a pessoa perguntou se o LibreOffice é obrigatório em produção para .doc/.xls/.ppt e se existe biblioteca alternativa. Inferência: instalar só libreoffice-writer, libreoffice-calc e libreoffice-impress com --no-install-recommends reduz a imagem para algo entre 400 e 600 MB (estimativa, não medida). Inferência: a alternativa é aceitar só .docx, .pptx e .xlsx e pedir que a pessoa salve em formato novo.

### Informações que talvez precisem ser guardadas

**Sinais para conversar depois, não confirmação:** Não identificado no texto original.

### Riscos e dependências

**Análise preliminar:** Medir o tamanho real da imagem antes de decidir. Mudar o escopo de formatos contraria a decisão do backlog que aceitou os formatos antigos. A SPEC-0028 (Docker) já prevê o LibreOffice na imagem; a otimização toca o Dockerfile de produção.

## Possíveis direções futuras

**Hipóteses para backlog ou spec, não requisitos:** Backlog de otimização da imagem (pacotes mínimos, medição de tamanho); ou revisão de escopo da SPEC-0023 para retirar os formatos antigos; ou usar xlrd só para .xls e manter o LibreOffice para .doc e .ppt.

## Pontos a revisar no futuro

**A revisar:** Qual o tamanho real da imagem com e sem o LibreOffice enxuto; se a equipe realmente recebe .doc/.ppt/.xls com frequência; se o tempo de conversão do LibreOffice é aceitável por documento; quem decide manter ou retirar os formatos antigos.

## Rastreabilidade

- Formulação original preservada integralmente nesta captura.
- Análises não substituem decisões do usuário.
- Backlogs e specs derivados devem referenciar este arquivo.

## Próximo passo

Manter em `specs/inbox/` ou refinar com `$specsfy-02-backlog`.
