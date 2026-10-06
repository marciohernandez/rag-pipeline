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
  splitters: ["header", "recursive"],
  limites: { chunk_size: { min: 200, max: 4000 }, chunk_overlap: { min: 0, max_fracao: 0.5 } },
};

export const rotulosSplitter: Record<string, string> = {
  header: "Markdown por cabeçalhos",
  recursive: "Recursivo por caracteres",
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
}

/** Valida tamanho (mínimo e máximo) e overlap (de 0 até a fração do tamanho). */
export function validarDivisao(tamanho: string, overlap: string, limites: Limites): ErrosDivisao {
  const erros: ErrosDivisao = {};
  const { min, max } = limites.chunk_size;
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
