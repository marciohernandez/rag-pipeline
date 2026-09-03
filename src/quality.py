"""Gate de qualidade da preparação: invariantes críticos e sinais (SPEC-0006).

Dois níveis, conforme a DEC-001 e a DEC-002. Um **invariante crítico** é
determinístico e interrompe a indexação levantando ``QualityGateError``. Um
**sinal de qualidade** é heurístico, entra no relatório e nunca interrompe.

Somente regra determinística bloqueia: uma heurística mal calibrada reprovaria
uma base saudável, e a evidência da fatia mostra que os defeitos heurísticos
convivem com recuperação aprovada.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4

from langchain_core.documents import Document

MINIMO_UTIL_PADRAO = 60

METADADOS_DE_RASTREABILIDADE = (
    "document_id",
    "source_hash",
    "project_id",
    "chunk_hash",
    "chunk_type",
)


class QualityGateError(RuntimeError):
    """Um invariante crítico falhou; a indexação não pode prosseguir."""


def conteudo_util(chunk: Document) -> str:
    """Texto do chunk sem o breadcrumb que o chunker injeta no ``page_content``.

    O breadcrumb é repetido dentro do conteúdo, então o comprimento bruto
    superestima o texto real: um chunk de 99 caracteres pode ter 40 de corpo.
    Toda avaliação de tamanho usa esta medida (DEC-008).
    """
    texto = chunk.page_content
    breadcrumb = chunk.metadata.get("breadcrumb") or ""
    if breadcrumb and texto.startswith(breadcrumb):
        texto = texto[len(breadcrumb) :]
    return texto.strip()


def _identificacao(chunk: Document) -> str:
    """Rótulo curto e sem segredo para apontar um chunk numa mensagem."""
    metadata = chunk.metadata
    return (
        metadata.get("chunk_id")
        or metadata.get("caminho_relativo")
        or metadata.get("nome_arquivo")
        or "chunk sem identificação"
    )


class CriticalInvariant(ABC):
    """Regra determinística cuja violação impede a indexação."""

    nome: str
    exige_manifesto: bool = False

    @abstractmethod
    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        """Devolve a descrição da violação ou ``None`` quando a regra passa."""


class ConjuntoNaoVazio(CriticalInvariant):
    nome = "conjunto_nao_vazio"

    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        if not chunks:
            return "Nenhum chunk foi gerado; indexação cancelada."
        return None


class IdentidadePresente(CriticalInvariant):
    nome = "chunk_id_presente"

    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        for chunk in chunks:
            if not str(chunk.metadata.get("chunk_id") or "").strip():
                return (
                    "Há chunk sem chunk_id em "
                    f"{chunk.metadata.get('caminho_relativo', 'documento desconhecido')}; "
                    "indexação cancelada."
                )
        return None


class IdentidadeUnica(CriticalInvariant):
    nome = "chunk_id_unico"

    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        vistos: set[str] = set()
        for chunk in chunks:
            chunk_id = str(chunk.metadata.get("chunk_id") or "")
            if chunk_id in vistos:
                return f"Há chunk_ids duplicados ({chunk_id}); indexação cancelada."
            vistos.add(chunk_id)
        return None


class ContagemDoManifesto(CriticalInvariant):
    nome = "contagem_do_manifesto"
    exige_manifesto = True

    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        if manifest is None:
            return None
        previstos = manifest.get("chunk_count")
        if previstos != len(chunks):
            return (
                "Contagem do manifesto é inconsistente: "
                f"{previstos} previstos contra {len(chunks)} chunks."
            )
        return None


class ConteudoAlemDoBreadcrumb(CriticalInvariant):
    nome = "conteudo_alem_do_breadcrumb"

    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        for chunk in chunks:
            if not conteudo_util(chunk):
                return (
                    f"O chunk {_identificacao(chunk)} não tem conteúdo além do "
                    "breadcrumb; indexação cancelada."
                )
        return None


class MetadadosDeRastreabilidade(CriticalInvariant):
    nome = "metadados_de_rastreabilidade"

    def violacao(self, chunks: list[Document], manifest: dict | None) -> str | None:
        for chunk in chunks:
            for metadado in METADADOS_DE_RASTREABILIDADE:
                if not str(chunk.metadata.get(metadado) or "").strip():
                    return (
                        f"O chunk {_identificacao(chunk)} está sem {metadado}; "
                        "indexação cancelada."
                    )
        return None


INVARIANTES_CRITICOS: tuple[CriticalInvariant, ...] = (
    ConjuntoNaoVazio(),
    IdentidadePresente(),
    IdentidadeUnica(),
    ContagemDoManifesto(),
    ConteudoAlemDoBreadcrumb(),
    MetadadosDeRastreabilidade(),
)


@dataclass(frozen=True)
class SizeThresholds:
    """Limites de tamanho de um documento.

    O máximo é derivado, não configurado: ``src/chunker.py`` deixa o frontmatter
    sobrescrever ``chunk_size`` por documento, então um teto global fixo passaria
    a acusar falso positivo assim que um arquivo declarasse outro valor (DEC-004).
    O mínimo não tem derivação natural e vem da configuração.
    """

    minimo_util: int
    maximo_derivado: int

    @classmethod
    def para_documento(
        cls,
        chunks: list[Document],
        chunking_cfg: dict,
        minimo_util: int,
    ) -> SizeThresholds:
        chunk_size = _chunk_size_efetivo(chunks, chunking_cfg)
        margem = max(
            (len(chunk.metadata.get("breadcrumb") or "") for chunk in chunks),
            default=0,
        )
        return cls(minimo_util=minimo_util, maximo_derivado=chunk_size + margem)


def _chunk_size_efetivo(chunks: list[Document], chunking_cfg: dict) -> int:
    """Reproduz a precedência de ``src/chunker.py``: frontmatter sobre config."""
    padrao = int(chunking_cfg.get("default_chunk_size", 1000))
    for chunk in chunks:
        declarado = chunk.metadata.get("chunk_size_recommended")
        if declarado:
            return int(declarado)
    return padrao


def _documento(chunk: Document) -> str:
    metadata = chunk.metadata
    return (
        metadata.get("caminho_relativo")
        or metadata.get("nome_arquivo")
        or "documento desconhecido"
    )


def _por_documento(chunks: list[Document]) -> dict[str, list[Document]]:
    agrupado: dict[str, list[Document]] = {}
    for chunk in chunks:
        agrupado.setdefault(_documento(chunk), []).append(chunk)
    return agrupado


PONTUACAO_FINAL = ".!?:;»\"`"

_ITEM_DE_LISTA = re.compile(r"^([-*+]|\d+[.)]|#{1,6})\s")
_PALAVRAS_COLADAS = re.compile(r"[a-zà-ú]{2,}[A-ZÀ-Ú][a-zà-ú]{2,}")

TAMANHO_MINIMO_DE_COLAGEM = 14


def _caminho_logico(chunk: Document) -> str:
    metadata = chunk.metadata
    return "|".join(
        str(metadata.get(chave, ""))
        for chave in ("titulo", "secao", "subsecao", "summary_key")
    )


class QualitySignal(ABC):
    """Regra heurística que entra no relatório e nunca interrompe a execução."""

    nome: str

    @abstractmethod
    def chunks_afetados(
        self, por_documento: dict[str, list[Document]], limiares: dict[str, SizeThresholds]
    ) -> dict[str, list[Document]]:
        """Devolve documento → chunks afetados, omitindo documento sem ocorrência."""

    def ocorrencias(
        self, por_documento: dict[str, list[Document]], limiares: dict[str, SizeThresholds]
    ) -> dict[str, int]:
        """Contagem por documento, derivada do detalhe."""
        return {
            caminho: len(chunks)
            for caminho, chunks in self.chunks_afetados(por_documento, limiares).items()
        }


class PerdaDeEstrutura(QualitySignal):
    """Chunks sem `secao`: o splitter não reconheceu os títulos do documento.

    Acontece quando a origem escreve heading dentro de bullet. Os títulos ficam
    invisíveis, os chunks colapsam sob um breadcrumb único e a recuperação perde
    a hierarquia que distingue um trecho do seguinte.
    """

    nome = "perda_de_estrutura"

    def chunks_afetados(self, por_documento, limiares):
        achados = {
            caminho: [chunk for chunk in chunks if not chunk.metadata.get("secao")]
            for caminho, chunks in por_documento.items()
        }
        return {caminho: lista for caminho, lista in achados.items() if lista}


class TruncamentoDeFrase(QualitySignal):
    """Chunk cujo texto termina sem completar a frase.

    Nasce do corte por tamanho e é invisível para qualquer regra de tamanho,
    porque o chunk continua dentro do limite. Lista, tabela e heading terminam
    legitimamente sem pontuação e são excluídos.
    """

    nome = "truncamento_de_frase"

    def _truncado(self, chunk: Document) -> bool:
        if chunk.metadata.get("chunk_type") == "section_summary":
            return False
        texto = conteudo_util(chunk).rstrip()
        if not texto:
            return False
        if texto[-1] in PONTUACAO_FINAL:
            return False
        if texto.endswith("---") or texto.endswith("|") or texto.endswith("```"):
            return False
        return not _ITEM_DE_LISTA.match(texto.split("\n")[-1].strip())

    def chunks_afetados(self, por_documento, limiares):
        achados = {
            caminho: [chunk for chunk in chunks if self._truncado(chunk)]
            for caminho, chunks in por_documento.items()
        }
        return {caminho: lista for caminho, lista in achados.items() if lista}


class DuplicataExata(QualitySignal):
    """Chunks com o mesmo conteúdo no mesmo caminho lógico.

    Não é falha de integridade: `chunk_id` distintos preservam a sincronização
    idempotente. É ruído no top-k, e costuma ser sintoma de estrutura perdida
    na origem (DEC-005).
    """

    nome = "duplicata_exata"

    def chunks_afetados(self, por_documento, limiares):
        resultado: dict[str, list[Document]] = {}
        for caminho, chunks in por_documento.items():
            grupos: dict[tuple[str, str], list[Document]] = {}
            for chunk in chunks:
                chave = (str(chunk.metadata.get("chunk_hash")), _caminho_logico(chunk))
                grupos.setdefault(chave, []).append(chunk)
            afetados = [
                chunk for grupo in grupos.values() if len(grupo) > 1 for chunk in grupo
            ]
            if afetados:
                resultado[caminho] = afetados
        return resultado


class TextoColapsado(QualitySignal):
    """Palavras coladas por colapso de tabulação na origem."""

    nome = "texto_colapsado"

    def _colapsado(self, chunk: Document) -> bool:
        return any(
            len(achado.group(0)) > TAMANHO_MINIMO_DE_COLAGEM
            for achado in _PALAVRAS_COLADAS.finditer(chunk.page_content)
        )

    def chunks_afetados(self, por_documento, limiares):
        achados = {
            caminho: [chunk for chunk in chunks if self._colapsado(chunk)]
            for caminho, chunks in por_documento.items()
        }
        return {caminho: lista for caminho, lista in achados.items() if lista}


class ConteudoUtilCurto(QualitySignal):
    """Conteúdo útil abaixo do mínimo configurado, descontado o breadcrumb."""

    nome = "conteudo_util_curto"

    def chunks_afetados(self, por_documento, limiares):
        resultado: dict[str, list[Document]] = {}
        for caminho, chunks in por_documento.items():
            minimo = limiares[caminho].minimo_util
            afetados = [c for c in chunks if len(conteudo_util(c)) < minimo]
            if afetados:
                resultado[caminho] = afetados
        return resultado


class TamanhoAcimaDoMaximo(QualitySignal):
    """Chunk acima do máximo derivado do `chunk_size` efetivo do documento."""

    nome = "tamanho_acima_do_maximo"

    def chunks_afetados(self, por_documento, limiares):
        resultado: dict[str, list[Document]] = {}
        for caminho, chunks in por_documento.items():
            maximo = limiares[caminho].maximo_derivado
            afetados = [c for c in chunks if len(c.page_content) > maximo]
            if afetados:
                resultado[caminho] = afetados
        return resultado


SINAIS_DE_QUALIDADE: tuple[QualitySignal, ...] = (
    PerdaDeEstrutura(),
    TruncamentoDeFrase(),
    DuplicataExata(),
    TextoColapsado(),
    ConteudoUtilCurto(),
    TamanhoAcimaDoMaximo(),
)


def distribuicao_de_tamanho(chunks: list[Document]) -> dict[str, dict[str, int]]:
    """Mínimo, mediana e máximo do conteúdo útil, por `chunk_type`."""
    por_tipo: dict[str, list[int]] = {}
    for chunk in chunks:
        tipo = str(chunk.metadata.get("chunk_type", "detail"))
        por_tipo.setdefault(tipo, []).append(len(conteudo_util(chunk)))
    resumo: dict[str, dict[str, int]] = {}
    for tipo, tamanhos in por_tipo.items():
        tamanhos.sort()
        resumo[tipo] = {
            "chunks": len(tamanhos),
            "minimo": tamanhos[0],
            "mediana": tamanhos[len(tamanhos) // 2],
            "maximo": tamanhos[-1],
        }
    return resumo


@dataclass
class QualityReport:
    """Resultado de uma avaliação, com o desfecho e o que foi observado.

    O eixo é o documento de origem, não o chunk: na base de referência o defeito
    se concentrou em dois de sete arquivos, e apontar o arquivo gera ação
    enquanto listar chunks curtos não (DEC-006). O detalhe por chunk fica no
    resultado estruturado, para quem precisar descer esse nível.
    """

    desfecho: str
    impedimento: str | None = None
    invariantes_avaliados: tuple[str, ...] = ()
    invariantes_pulados: tuple[str, ...] = ()
    avisos: tuple[str, ...] = ()
    documentos: dict = field(default_factory=dict)
    sinais: dict = field(default_factory=dict)
    limiares_aplicados: dict = field(default_factory=dict)
    chunks: list = field(default_factory=list)
    run_id: str = ""
    gerado_em: str = ""
    report_path: str | None = None

    def to_dict(self) -> dict:
        """Resultado estruturado. Não carrega credencial nem destino remoto."""
        return {
            "run_id": self.run_id,
            "gerado_em": self.gerado_em,
            "desfecho": self.desfecho,
            "impedimento": self.impedimento,
            "invariantes_avaliados": list(self.invariantes_avaliados),
            "invariantes_pulados": list(self.invariantes_pulados),
            "avisos": list(self.avisos),
            "limiares_aplicados": self.limiares_aplicados,
            "sinais": self.sinais,
            "documentos": self.documentos,
            "chunks": self.chunks,
        }

    def render(self) -> str:
        """Relatório legível, agrupado por documento de origem."""
        linhas = [
            "Gate de qualidade da preparação",
            f"Desfecho: {self.desfecho}",
        ]
        if self.impedimento:
            linhas.append(f"Impedimento: {self.impedimento}")
        linhas.append(
            f"Invariantes avaliados: {len(self.invariantes_avaliados)}"
            + (
                f" | pulados: {', '.join(self.invariantes_pulados)}"
                if self.invariantes_pulados
                else ""
            )
        )
        distribuicao = self.sinais.get("distribuicao_de_tamanho", {})
        if distribuicao:
            linhas.append("")
            linhas.append("Distribuição de conteúdo útil por tipo de chunk:")
            for tipo, medidas in sorted(distribuicao.items()):
                linhas.append(
                    f"  {tipo}: {medidas['chunks']} chunks, "
                    f"mínimo {medidas['minimo']}, mediana {medidas['mediana']}, "
                    f"máximo {medidas['maximo']}"
                )

        linhas.append("")
        linhas.append("Sinais por documento de origem:")
        afetados = {
            caminho: dados
            for caminho, dados in self.documentos.items()
            if dados.get("sinais")
        }
        if not afetados:
            linhas.append("  Nenhum sinal de qualidade encontrado.")
        for caminho, dados in sorted(afetados.items()):
            detalhe = ", ".join(
                f"{nome}={total}" for nome, total in sorted(dados["sinais"].items())
            )
            linhas.append(f"  {caminho} ({dados['chunks']} chunks): {detalhe}")
        saudaveis = len(self.documentos) - len(afetados)
        if saudaveis:
            linhas.append(f"  {saudaveis} documento(s) sem nenhum sinal.")

        for aviso in self.avisos:
            linhas.append(f"Aviso: {aviso}")
        return "\n".join(linhas)


def evaluate_quality(
    chunks: list[Document],
    chunking_cfg: dict,
    quality_cfg: dict,
    *,
    manifest: dict | None = None,
    output_dir: Path | str | None = None,
) -> QualityReport:
    """Avalia o conjunto local antes de qualquer escrita no vector store.

    Levanta ``QualityGateError`` quando um invariante crítico falha. O
    invariante de contagem só é avaliado quando há manifesto: no comando de
    diagnóstico ele não existe, e a ausência não reprova a base (DEC-009).
    """
    avaliados: list[str] = []
    pulados: list[str] = []
    avisos: list[str] = []

    for invariante in INVARIANTES_CRITICOS:
        if invariante.exige_manifesto and manifest is None:
            pulados.append(invariante.nome)
            avisos.append(
                f"Invariante {invariante.nome} pulado por ausência de manifesto."
            )
            continue
        violacao = invariante.violacao(chunks, manifest)
        avaliados.append(invariante.nome)
        if violacao:
            raise QualityGateError(violacao)

    minimo_util = int(quality_cfg.get("minimo_util") or MINIMO_UTIL_PADRAO)
    if not quality_cfg.get("minimo_util"):
        avisos.append(
            f"Mínimo de conteúdo útil não configurado; aplicado o padrão de "
            f"{MINIMO_UTIL_PADRAO} caracteres."
        )

    por_documento = _por_documento(chunks)
    limiares = {
        caminho: SizeThresholds.para_documento(do_documento, chunking_cfg, minimo_util)
        for caminho, do_documento in por_documento.items()
    }

    # Cada sinal é avaliado uma única vez. A contagem por documento e o detalhe
    # por chunk derivam do mesmo resultado, para que não possam divergir.
    afetados_por_sinal = {
        sinal.nome: sinal.chunks_afetados(por_documento, limiares)
        for sinal in SINAIS_DE_QUALIDADE
    }

    sinais: dict = {
        nome: {caminho: len(atingidos) for caminho, atingidos in por_caminho.items()}
        for nome, por_caminho in afetados_por_sinal.items()
    }
    sinais["distribuicao_de_tamanho"] = distribuicao_de_tamanho(chunks)

    sem_secao = afetados_por_sinal[PerdaDeEstrutura.nome]
    documentos = {
        caminho: {
            "chunks": len(do_documento),
            "sem_secao": len(sem_secao.get(caminho, ())),
            "sem_subsecao": sum(
                1 for chunk in do_documento if not chunk.metadata.get("subsecao")
            ),
            "minimo_util": limiares[caminho].minimo_util,
            "maximo_derivado": limiares[caminho].maximo_derivado,
            "sinais": {
                nome: contagem[caminho]
                for nome, contagem in sinais.items()
                if nome != "distribuicao_de_tamanho" and caminho in contagem
            },
        }
        for caminho, do_documento in por_documento.items()
    }

    detalhe_por_chunk: dict[str, dict] = {}
    for nome, por_caminho in afetados_por_sinal.items():
        for caminho, atingidos in por_caminho.items():
            for chunk in atingidos:
                registro = detalhe_por_chunk.setdefault(
                    str(chunk.metadata.get("chunk_id")),
                    {
                        "chunk_id": chunk.metadata.get("chunk_id"),
                        "documento": caminho,
                        "conteudo_util": len(conteudo_util(chunk)),
                        "tamanho_bruto": len(chunk.page_content),
                        "sinais": [],
                    },
                )
                registro["sinais"].append(nome)

    relatorio = QualityReport(
        desfecho="aprovado",
        invariantes_avaliados=tuple(avaliados),
        invariantes_pulados=tuple(pulados),
        avisos=tuple(avisos),
        documentos=documentos,
        sinais=sinais,
        limiares_aplicados={"minimo_util": minimo_util},
        chunks=sorted(detalhe_por_chunk.values(), key=lambda item: item["documento"]),
        run_id=str(uuid4()),
        gerado_em=datetime.now(UTC).isoformat(),
    )

    if output_dir is not None:
        try:
            relatorio.report_path = str(_gravar(relatorio, Path(output_dir)))
        except OSError as error:
            # A avaliação já terminou: uma falha de escrita não pode mascarar o
            # desfecho nem apagar o relatório legível. `strerror` descreve a
            # causa sem devolver o caminho completo à saída.
            relatorio.report_path = None
            relatorio.avisos = relatorio.avisos + (
                "Falha ao gravar o resultado estruturado: "
                f"{error.strerror or type(error).__name__}.",
            )
    return relatorio


def _gravar(relatorio: QualityReport, output_dir: Path) -> Path:
    """Grava o resultado estruturado em arquivo próprio da execução.

    Fica fora do `manifest.json`, que preserva sua responsabilidade única de
    identidade e contagens (DEC-007).
    """
    destino = output_dir / f"quality-{relatorio.run_id}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=destino.parent, delete=False, suffix=".tmp"
    ) as temporario:
        json.dump(relatorio.to_dict(), temporario, ensure_ascii=False, indent=2)
        parcial = Path(temporario.name)
    parcial.replace(destino)
    return destino
