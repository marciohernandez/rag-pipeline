"""Testes TDD da SPEC-0005 — neutralidade de cliente nas ferramentas operacionais.

Arquivo próprio, conforme a DEC-008: os marcadores desta fatia não podem se
misturar aos das specs anteriores na contagem de cobertura.

O Gherkin da seção 6 da spec é a referência de comportamento; nenhum arquivo
``.feature`` é criado ou executado aqui.

Contrato definido por estes casos e materializado pelas tarefas T015 a T021:

``src.pipeline.indexing``
    ``resolve_identity(cfg) -> BaseIdentity`` com ``nome``, ``descricao`` e
    ``descricao_derivada``; exige ``projeto.nome`` e degrada ``projeto.descricao``
    ausente ou vazia para ``DESCRICAO_NEUTRA``, avisando por log.
    ``resolve_default_question(cfg) -> tuple[str, bool]`` devolve a primeira
    consulta do gabarito de ``caminhos.consultas_referencia`` e degrada para
    ``PERGUNTA_NEUTRA`` com aviso quando o gabarito não puder ser lido.

``chat``
    ``montar_abertura(identidade) -> str`` e
    ``montar_template_sistema(identidade) -> str``.

``demo_rag``
    ``montar_prompt(identidade, contexto, pergunta) -> str``.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
FERRAMENTAS = ("chat.py", "demo_rag.py", "search.py")

# Nome próprio e conteúdo de domínio bancário. R-001 localizou oito ocorrências
# nos três arquivos; a lista alcança as duas formas porque a guarda estática
# sozinha não protege contra um cliente ainda não catalogado.
IDENTIFICADORES_DE_CLIENTE = (
    "c6 bank",
    "c6 empresas",
    "rag c6",
    "conta pj",
    "cheque especial",
    "vivo fibra",
    "vivo gold",
    "vivo_gold",
)

DEPENDENCIAS_BASELINE_ESPERADAS = frozenset({"NFR-001"})


def _fonte(nome: str) -> str:
    return (RAIZ / nome).read_text(encoding="utf-8")


def _carregar_modulo(nome: str):
    """Importa uma ferramenta preservando ``sys.stdout``.

    ``chat.py`` troca ``sys.stdout`` no import; sem a restauração o pytest
    perde a captura das demais provas.
    """
    original = sys.stdout
    try:
        modulo = importlib.import_module(nome)
    finally:
        sys.stdout = original
    return modulo


def _atributo(modulo, nome: str, motivo: str):
    alvo = getattr(modulo, nome, None)
    assert callable(alvo), f"{modulo.__name__}.{nome} ausente: {motivo}"
    return alvo


def _config(
    nome="Base_Ficticia_Alfa",
    descricao="acervo ficticio sobre bicicletas urbanas",
    gabarito=None,
):
    cfg: dict = {"projeto": {}, "caminhos": {}}
    if nome is not None:
        cfg["projeto"]["nome"] = nome
    if descricao is not None:
        cfg["projeto"]["descricao"] = descricao
    if gabarito is not None:
        cfg["caminhos"]["consultas_referencia"] = str(gabarito)
    return cfg


def _gabarito(tmp_path: Path, pergunta: str) -> Path:
    destino = tmp_path / "consultas.yaml"
    destino.write_text(
        yaml.safe_dump(
            [
                {"pergunta": pergunta, "categoria": "especifica", "deve_conter": ["aro 29"]},
                {
                    "pergunta": "quais modelos existem?",
                    "categoria": "ampla",
                    "deve_conter": ["modelo"],
                },
            ],
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return destino


def _indexing():
    return importlib.import_module("src.pipeline.indexing")


def _saida_deriva_da_configuracao(saida: str, nome: str, descricao: str) -> bool:
    """Discriminador da guarda positiva: independe do nome do cliente."""
    return nome in saida and descricao in saida


def _git_ls_files() -> set[str]:
    if not (RAIZ / ".git").exists():
        pytest.fail(
            "Diretório de controle de versão ausente: a prova do índice do Git "
            "não pode passar por vacuidade nesta cópia."
        )
    executado = subprocess.run(
        ["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    assert executado.returncode == 0, f"git ls-files falhou: {executado.stderr.strip()}"
    return {linha.strip() for linha in executado.stdout.splitlines() if linha.strip()}


def _ocorrencias(nome: str) -> list[str]:
    conteudo = _fonte(nome).lower()
    return [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in conteudo]


def test_ac_001_abertura_e_prompt_do_chat_citam_a_configuracao() -> None:
    # SPECSFY: US-001 FR-001 NFR-001 AC-001
    cfg = _config()
    indexing = _indexing()
    resolver = _atributo(
        indexing,
        "resolve_identity",
        "a identidade ainda não é derivada da configuração",
    )
    identidade = resolver(cfg)

    chat = _carregar_modulo("chat")
    abertura = _atributo(
        chat, "montar_abertura", "a abertura ainda é um literal de cliente"
    )(identidade)
    template = _atributo(
        chat,
        "montar_template_sistema",
        "o prompt ainda é um literal de cliente",
    )(identidade)

    assert cfg["projeto"]["nome"] in abertura
    assert cfg["projeto"]["descricao"] in template
    saida = f"{abertura}\n{template}".lower()
    assert [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in saida] == []


def test_ac_002_prompt_do_demonstrativo_reflete_a_configuracao() -> None:
    # SPECSFY: US-001 FR-001 FR-002 AC-002
    cfg = _config()
    indexing = _indexing()
    identidade = _atributo(indexing, "resolve_identity", "a identidade ainda não é derivada")(cfg)

    demo = _carregar_modulo("demo_rag")
    montar = _atributo(
        demo,
        "montar_prompt",
        "o prompt do demonstrativo ainda é um literal de cliente",
    )
    prompt = montar(
        identidade,
        "[Fonte: exemplo.md]\nconteudo ficticio",
        "qual o aro da bicicleta?",
    )

    assert cfg["projeto"]["nome"] in prompt
    assert cfg["projeto"]["descricao"] in prompt
    assert [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in prompt.lower()] == []


def test_ac_003_pergunta_padrao_vem_da_primeira_consulta_do_gabarito(tmp_path: Path) -> None:
    # SPECSFY: US-001 FR-002 NFR-003 AC-003
    pergunta = "qual o aro recomendado para uso urbano?"
    cfg = _config(gabarito=_gabarito(tmp_path, pergunta))
    indexing = _indexing()
    resolver = _atributo(
        indexing,
        "resolve_default_question",
        "a pergunta padrão ainda é um literal",
    )

    escolhida, derivada = resolver(cfg)
    assert escolhida == pergunta
    assert derivada is True

    demo = _carregar_modulo("demo_rag")
    literal = getattr(demo, "PERGUNTA_PADRAO", "")
    assert not [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in str(literal).lower()]


def test_ac_004_gabarito_inexistente_degrada_com_aviso(tmp_path: Path, caplog) -> None:
    # SPECSFY: FR-002 FR-003 AC-004
    indexing = _indexing()
    resolver = _atributo(
        indexing,
        "resolve_default_question",
        "não há resolução da pergunta padrão",
    )
    neutra = getattr(indexing, "PERGUNTA_NEUTRA", None)
    assert isinstance(neutra, str) and neutra, "PERGUNTA_NEUTRA ausente em src/pipeline/indexing.py"

    ausente = tmp_path / "nao_existe.yaml"
    malformado = tmp_path / "vazio.yaml"
    malformado.write_text("[]", encoding="utf-8")

    for cfg in (_config(gabarito=ausente), _config(gabarito=malformado), _config()):
        caplog.clear()
        with caplog.at_level("WARNING"):
            escolhida, derivada = resolver(cfg)
        assert escolhida == neutra
        assert derivada is False
        assert caplog.records, "o operador não foi avisado da degradação da pergunta"


def test_ac_005_descricao_vazia_degrada_com_aviso(caplog) -> None:
    # SPECSFY: US-001 FR-001 FR-003 AC-005
    indexing = _indexing()
    resolver = _atributo(indexing, "resolve_identity", "a identidade ainda não é derivada")
    neutra = getattr(indexing, "DESCRICAO_NEUTRA", None)
    assert isinstance(neutra, str) and neutra, (
        "DESCRICAO_NEUTRA ausente em src/pipeline/indexing.py"
    )

    for cfg in (_config(descricao=""), _config(descricao=None)):
        caplog.clear()
        with caplog.at_level("WARNING"):
            identidade = resolver(cfg)
        assert identidade.descricao == neutra
        assert identidade.descricao_derivada is False
        assert caplog.records, "o operador não foi avisado da degradação da descrição"


def test_ac_006_nome_ausente_encerra_com_mensagem_clara() -> None:
    # SPECSFY: FR-003 FR-005 AC-006
    indexing = _indexing()
    resolver = _atributo(indexing, "resolve_identity", "a identidade ainda não é derivada")

    for cfg in (_config(nome=None), _config(nome="   ")):
        with pytest.raises(ValueError) as erro:
            resolver(cfg)
        mensagem = str(erro.value)
        assert "projeto.nome" in mensagem
        assert not [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in mensagem.lower()]


def test_ac_007_config_de_uso_fora_do_indice_do_git() -> None:
    # SPECSFY: US-002 FR-004 AC-007
    versionados = _git_ls_files()
    assert "config.yaml" not in versionados, "config.yaml ainda está versionado"
    assert "config.yaml" in _fonte(".gitignore"), ".gitignore não exclui config.yaml"
    assert (RAIZ / "config.yaml").is_file(), "a configuração de uso precisa permanecer em disco"


def test_ac_008_exemplo_versionado_e_neutro() -> None:
    # SPECSFY: US-002 FR-004 AC-008
    versionados = _git_ls_files()
    assert "config.example.yaml" in versionados, "config.example.yaml não está versionado"

    exemplo = _fonte("config.example.yaml")
    minusculo = exemplo.lower()
    assert [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in minusculo] == []

    carregado = yaml.safe_load(exemplo) or {}
    vetor = carregado.get("vector_store", {})
    real = yaml.safe_load(_fonte("config.yaml")) or {}
    vetor_real = real.get("vector_store", {})
    for chave in ("collection_name", "namespace"):
        assert vetor.get(chave) != vetor_real.get(chave), (
            f"o exemplo publica o {chave} real do destino"
        )


def test_ac_009_procedimento_de_primeira_configuracao_publicado() -> None:
    # SPECSFY: US-002 FR-004 FR-006 AC-009
    readme = _fonte("README.md")
    assert "config.example.yaml" in readme, "README.md não cita o exemplo de configuração"
    assert ".env.example" in readme, "o passo de segredos deixou de ser publicado"

    linhas = readme.splitlines()
    posicao_exemplo = next(i for i, linha in enumerate(linhas) if "config.example.yaml" in linha)
    posicao_env = next(i for i, linha in enumerate(linhas) if ".env.example" in linha)
    assert abs(posicao_exemplo - posicao_env) <= 12, (
        "o passo de copiar a configuração não aparece junto do passo equivalente de segredos"
    )


def test_ac_010_guarda_estatica_nao_encontra_identificador_de_cliente() -> None:
    # SPECSFY: US-003 FR-005 NFR-003 AC-010
    vazamentos = {nome: _ocorrencias(nome) for nome in FERRAMENTAS if _ocorrencias(nome)}
    assert vazamentos == {}, f"identidade de cliente ainda escrita nas ferramentas: {vazamentos}"


def test_ac_011_guarda_positiva_reprova_identidade_fixa() -> None:
    # SPECSFY: US-003 FR-005 NFR-002 AC-011
    # O nome abaixo não pertence à lista de proibições: a reprovação precisa
    # independer do cliente reintroduzido.
    cfg = _config(nome="Banco Futuro S.A.", descricao="acervo ficticio de um cliente novo")
    indexing = _indexing()
    identidade = _atributo(indexing, "resolve_identity", "não há ponto único de derivação")(cfg)

    chat = _carregar_modulo("chat")
    template = _atributo(
        chat,
        "montar_template_sistema",
        "o prompt não é composto pela identidade",
    )(identidade)
    assert _saida_deriva_da_configuracao(
        template, cfg["projeto"]["nome"], cfg["projeto"]["descricao"]
    )

    fixo = "Voce e um assistente especialista nos produtos do Banco Futuro S.A."
    assert not _saida_deriva_da_configuracao(
        fixo, cfg["projeto"]["nome"], cfg["projeto"]["descricao"]
    ), "a guarda positiva aceitou uma identidade fixa"


def test_ac_012_entrega_nao_altera_dependencias_nem_fronteiras() -> None:
    # SPECSFY: US-003 NFR-001 NFR-002 NFR-003 AC-012
    manifesto = tomllib.loads(_fonte("pyproject.toml"))
    declaradas = set(manifesto["project"]["dependencies"])
    # SPEC-0010: ChromaDB e Pinecone removidos; abstração multi-provider mantida.
    # SPEC-0012: backend de aplicação acrescenta FastAPI, PostgreSQL (psycopg/alembic),
    # Procrastinate, Cloudflare R2 (boto3) e python-multipart (upload de arquivos).
    # SPEC-0012 Fase 9: uvicorn declarado como servidor ASGI do entrypoint FastAPI
    # (o README manda `uv run uvicorn src.app.main:app`).
    # SPEC-0023: conversão de documentos (PDF/DOCX/PPTX/XLSX/imagem) acrescenta as
    # primeiras bibliotecas de extração — nenhuma delas é um provider de LLM,
    # embeddings ou vector store, então a neutralidade de cliente permanece intacta.
    baseline = {
        "alembic>=1.19.2",
        "argon2-cffi>=25.1.0",
        "boto3>=1.43.88",
        # SPEC-0036/DEC-003: extração local de HTML, sem novo provider.
        "beautifulsoup4>=4.15.0",
        "markdownify>=1.2.3",
        # SPEC-0026: cifra Fernet das chaves das conexões de ingestão.
        "cryptography>=50.0.2",
        "fastapi>=0.141.1",
        "langchain>=1.2.18",
        "langchain-community>=0.4.1",
        "langchain-huggingface>=1.2.2",
        "langchain-openai>=1.2.1",
        # SPEC-0021: LangGraph declarado como dependência direta (orquestração do assistente).
        "langgraph>=1",
        "openai>=2.36.0",
        "openpyxl>=3.1.5",
        "pillow>=12.3.0",
        "procrastinate>=3.9.0",
        "psycopg[binary]>=3.3.5",
        "pymupdf4llm>=1.28.2",
        "pytesseract>=0.3.13",
        "python-docx>=1.2.0",
        "python-dotenv>=1.2.2",
        "python-multipart>=0.0.32",
        "python-pptx>=1.0.2",
        "pyyaml>=6.0.3",
        "qdrant-client==1.10.1",
        "tiktoken>=0.12.0",
        "uvicorn>=0.34.0",
    }
    assert declaradas == baseline, f"dependências divergem da baseline: {declaradas ^ baseline}"

    indexing = _indexing()
    assert callable(getattr(indexing, "resolve_identity", None)), (
        "a guarda positiva não tem sujeito: src/pipeline/indexing.py não expõe a derivação"
    )
    fronteira = _fonte("tests/test_provider_boundaries.py")
    assert "chat.py" in fronteira, "a exceção rastreada de ChatOpenAI deixou de ser verificada"


def test_ac_013_documentacao_nao_declara_mais_a_limitacao() -> None:
    # SPECSFY: FR-006 NFR-002 AC-013
    guia = _fonte("GUIA_DE_USO.md")
    minusculo = guia.lower()
    assert [marca for marca in IDENTIFICADORES_DE_CLIENTE if marca in minusculo] == [], (
        "GUIA_DE_USO.md ainda declara a identidade fixa como limitação conhecida"
    )
    assert "configuração" in minusculo or "configuracao" in minusculo


def test_ac_014_varredura_documental_alcanca_o_exemplo() -> None:
    # SPECSFY: FR-006 NFR-001 AC-014
    varredura = _fonte("tests/test_docs_safety.py")
    assert '"config.example.yaml"' in varredura, (
        "a varredura de material publicado não alcança o exemplo versionado"
    )
    assert '"config.yaml"' not in varredura, (
        "a varredura ainda aponta para um arquivo fora do controle de versão"
    )
    for publicado in ("README.md", "GUIA_DE_USO.md", "CONTEXTO_MELHORIA_RECUPERACAO_RAG.md"):
        assert f'"{publicado}"' in varredura, f"{publicado} deixou de ser verificado"
