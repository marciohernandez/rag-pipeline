/**
 * Limites e validações do fluxo de ingestão (SPEC-0026). Os limites de arquivo
 * espelham `src/app/ingestao.py`; os de divisão vêm de `GET /ingestao/padroes`,
 * e este módulo guarda só o fallback usado enquanto o endpoint responde.
 */

export const MAX_ARQUIVOS = 50;
export const MAX_BYTES_ARQUIVO = 5 * 1024 * 1024;
export const MAX_BYTES_TOTAL = 50 * 1024 * 1024;

export interface Limites {
  chunk_size: { min: number; max: number };
  chunk_overlap: { min: number; max_fracao: number };
  token_size?: { min: number; max: number };
}

/** Escolhas de processamento além da divisão básica (SPEC-0029), enviadas como JSON. */
export interface Processamento {
  opcoes: {
    /** `null` usa o padrão da estratégia: Desativado no Markdown recursivo, H3 nas demais. */
    nivel_cabecalho: number | null;
    separador: string;
    encoding: string;
    remover_cabecalhos: boolean;
  };
  resumos: { ativo: boolean; minimo_subsecoes: number };
  qualidade: { minimo_util: number };
  contrato: { status_bloqueado: string[] };
  destino: { batch_size: number };
}

export const PROCESSAMENTO_PADRAO: Processamento = {
  opcoes: { nivel_cabecalho: null, separador: "\\n\\n", encoding: "cl100k_base", remover_cabecalhos: false },
  resumos: { ativo: true, minimo_subsecoes: 3 },
  qualidade: { minimo_util: 60 },
  contrato: { status_bloqueado: [] },
  destino: { batch_size: 50 },
};

export const ENCODINGS = ["cl100k_base", "o200k_base"];
export const TAMANHOS_DE_PAGINA = [10, 20, 50, 75, 100];

/** Campos que cada estratégia usa; os demais ficam ocultos na etapa Divisão. */
export const CAMPOS_POR_ESTRATEGIA: Record<string, string[]> = {
  header: ["tamanho", "overlap", "nivel_cabecalho", "resumos"],
  markdown: ["tamanho", "overlap", "nivel_cabecalho"],
  markdown_syntax: ["nivel_cabecalho", "remover_cabecalhos", "resumos"],
  recursive: ["tamanho", "overlap"],
  character_split: ["tamanho", "overlap", "separador"],
  token: ["tamanho", "overlap", "encoding"],
};

export function nivelEfetivo(splitter: string, processamento: Processamento): number {
  return processamento.opcoes.nivel_cabecalho ?? (splitter === "markdown" ? 0 : 3);
}

/** JSON do campo `processamento`, com o nível de cabeçalho já resolvido para a estratégia. */
export function serializarProcessamento(splitter: string, processamento: Processamento): string {
  return JSON.stringify({
    ...processamento,
    opcoes: { ...processamento.opcoes, nivel_cabecalho: nivelEfetivo(splitter, processamento) },
  });
}

export interface Padroes {
  splitter: string;
  chunk_size: number;
  chunk_overlap: number;
  splitters: string[];
  limites: Limites;
}

export const PADROES_FALLBACK: Padroes = {
  splitter: "header",
  chunk_size: 1000,
  chunk_overlap: 200,
  splitters: ["header", "markdown", "markdown_syntax", "recursive", "character_split", "token"],
  limites: {
    chunk_size: { min: 200, max: 4000 },
    chunk_overlap: { min: 0, max_fracao: 0.5 },
    token_size: { min: 50, max: 2000 },
  },
};

export const rotulosSplitter: Record<string, string> = {
  header: "Markdown por cabeçalhos",
  markdown: "Markdown recursivo",
  markdown_syntax: "Markdown sintático",
  recursive: "Recursivo por caracteres",
  character_split: "Por caractere",
  token: "Por tokens",
};

/** Mensagem do primeiro problema encontrado ao juntar arquivos à seleção. */
export function validarArquivos(atuais: File[], novos: File[]): string | null {
  const todos = [...atuais, ...novos];
  if (todos.length > MAX_ARQUIVOS) return `Limite de ${MAX_ARQUIVOS} arquivos excedido.`;
  let total = 0;
  for (const arquivo of todos) {
    if (!arquivo.name.endsWith(".md")) return `Extensão inválida: ${arquivo.name}. Envie arquivos .md.`;
    if (arquivo.size > MAX_BYTES_ARQUIVO) return `O arquivo ${arquivo.name} excede o limite de 5 MB.`;
    total += arquivo.size;
  }
  if (total > MAX_BYTES_TOTAL) return "Limite de 50 MB por envio excedido.";
  return null;
}

export interface ErrosDivisao {
  tamanho?: string;
  overlap?: string;
  separador?: string;
}

/**
 * Valida tamanho (mínimo e máximo, em tokens na estratégia por tokens) e overlap
 * (de 0 até a fração do tamanho). O Markdown sintático não usa tamanho.
 */
export function validarDivisao(
  tamanho: string,
  overlap: string,
  limites: Limites,
  splitter = "header",
  processamento: Processamento = PROCESSAMENTO_PADRAO,
): ErrosDivisao {
  const erros: ErrosDivisao = {};
  if (splitter === "character_split") {
    const separador = processamento.opcoes.separador;
    if (separador.length < 1 || separador.length > 10) erros.separador = "O separador deve ter de 1 a 10 caracteres.";
  }
  if (!(CAMPOS_POR_ESTRATEGIA[splitter] ?? ["tamanho"]).includes("tamanho")) return erros;
  const { min, max } = splitter === "token" ? (limites.token_size ?? { min: 50, max: 2000 }) : limites.chunk_size;
  const valorTamanho = Number(tamanho);
  if (!tamanho.trim() || !Number.isInteger(valorTamanho) || valorTamanho < min || valorTamanho > max) {
    erros.tamanho = `O tamanho do chunk tem mínimo de ${min} e máximo de ${max}.`;
  }
  const valorOverlap = Number(overlap);
  const teto = Math.floor(valorTamanho * limites.chunk_overlap.max_fracao);
  if (!overlap.trim() || !Number.isInteger(valorOverlap) || valorOverlap < 0) {
    erros.overlap = "O overlap deve ser um inteiro de 0 em diante.";
  } else if (!erros.tamanho && valorOverlap > teto) {
    erros.overlap = `O overlap pode ir de 0 até a metade do tamanho (${teto}).`;
  }
  return erros;
}
