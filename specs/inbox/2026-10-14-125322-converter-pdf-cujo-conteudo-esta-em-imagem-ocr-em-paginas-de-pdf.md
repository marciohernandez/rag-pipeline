# Inbox: Converter PDF cujo conteúdo está em imagem (OCR em páginas de PDF)

| Metadado | Valor |
| --- | --- |
| Status | Capturada |
| Capturada em | 2026-10-14T12:53:22Z |
| Slug | converter-pdf-cujo-conteudo-esta-em-imagem-ocr-em-paginas-de-pdf |
| Origem | Recriada a partir da memória do projeto (`pdf-com-conteudo-em-imagem`); a captura original não foi gravada |
| Processamento | Recriação sem perguntas |
| Backlog derivado | Nenhum |
| Spec derivada | Nenhuma |

## Texto original

Relato preservado da memória do projeto, não literal da pessoa:

O conversor de PDF (`pymupdf4llm`, SPEC-0023) só lê a camada de texto. Um PDF de página web impressa gerou um `.md` só com o parágrafo do topo, perdendo o resto, que é imagem dentro do PDF. A pessoa disse que receber documentos assim é muito comum e que isso deve estar previsto e funcionando.

## Análise inicial

- **Declaração:** PDFs com conteúdo em imagem são comuns e devem funcionar.
- **Declaração:** o exemplo observado saiu quase vazio, só com o parágrafo do topo.
- **Inferência:** o FR-003 da SPEC-0023 prevê OCR só para arquivos de imagem (JPG/PNG), não para páginas de PDF. É lacuna de produto, não bug de tabela.
- **Fato do código:** `src/pipeline/conversion/converters/pdf.py` usa só `pymupdf4llm`; `converters/image.py` já usa `pytesseract`, e o Tesseract está instalado em `/usr/bin/tesseract`.
- **Restrição:** o PDF de exemplo tem dados pessoais; não versionar nem usar como fixture.
- **Aberto:** detecção de página sem texto, idioma do OCR, custo de tempo, como sinalizar qualidade ao usuário.
