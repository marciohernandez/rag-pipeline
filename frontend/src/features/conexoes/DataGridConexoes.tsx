"use client";

import type { KeyboardEvent, MouseEvent } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";

export interface ConexaoResumo {
  id: string;
  nome: string;
  tipo: string;
  situacao: string;
  configuracao?: { modelo?: string; dimensoes?: number; url_base?: string; url?: string };
  segredo_definido: boolean;
  segredo_mascara: string;
  em_uso: number;
  criado_em?: string | null;
  atualizada_em?: string | null;
}

export const rotulosTipo: Record<string, string> = {
  embeddings_openai: "Embeddings OpenAI",
  qdrant: "Qdrant",
};

interface Props {
  conexoes: ConexaoResumo[];
  carregando?: boolean;
  onEditar?: (conexao: ConexaoResumo) => void;
  onAlternarSituacao?: (conexao: ConexaoResumo) => void;
  onExcluir?: (conexao: ConexaoResumo) => void;
}

const COLUNAS = ["ID", "Nome", "Tipo", "Situação", "Chave"];

/**
 * Listagem de conexões (SPEC-0026, FR-012): largura inteira, coluna ID, linha
 * inteira como link para o detalhe e ações independentes da linha. A chave
 * nunca é exibida; só a máscara que o backend devolve.
 */
export default function DataGridConexoes({
  conexoes,
  carregando = false,
  onEditar,
  onAlternarSituacao,
  onExcluir,
}: Props) {
  const router = useRouter();
  function abrir(id: string) {
    router.push(`/conexoes/${id}`);
  }
  function tecla(evento: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      abrir(id);
    }
  }
  function acao(evento: MouseEvent) {
    evento.stopPropagation();
  }

  return (
    <div
      className="w-full min-w-0 max-w-full overflow-hidden rounded-lg border"
      style={{ contain: "inline-size paint" }}
    >
      {carregando ? (
        <IndicadorProcessamento className="px-3 py-2.5">Carregando conexões</IndicadorProcessamento>
      ) : null}
      <div className="w-full min-w-0 overflow-x-auto">
        <table className="w-full min-w-[58rem] border-collapse text-sm" aria-busy={carregando}>
          <caption className="sr-only">Conexões de ingestão da equipe ativa</caption>
          <thead>
            <tr className="border-b bg-muted/40 text-left">
              {COLUNAS.map((nome) => (
                <th key={nome} scope="col" className="px-3 py-2 font-medium text-muted-foreground">
                  {nome}
                </th>
              ))}
              <th scope="col">
                <span className="sr-only">Ações</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {carregando ? (
              Array.from({ length: 3 }).map((_, i) => (
                <tr key={i} className="border-b">
                  {Array.from({ length: COLUNAS.length + 1 }).map((__, j) => (
                    <td key={j} className="px-3 py-2.5">
                      <Skeleton className="h-4 w-24" />
                    </td>
                  ))}
                </tr>
              ))
            ) : conexoes.length === 0 ? (
              <tr>
                <td colSpan={COLUNAS.length + 1} className="px-3 py-10 text-center text-muted-foreground">
                  Nenhuma conexão cadastrada.
                </td>
              </tr>
            ) : (
              conexoes.map((conexao) => {
                const ativa = conexao.situacao === "ativa";
                return (
                  <tr
                    key={conexao.id}
                    tabIndex={0}
                    aria-label={`Conexão ${conexao.nome}`}
                    onClick={() => abrir(conexao.id)}
                    onKeyDown={(e) => tecla(e, conexao.id)}
                    className={`cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring ${ativa ? "" : "opacity-65"}`}
                  >
                    <td className="px-3 py-2.5 font-mono text-xs">{conexao.id}</td>
                    <td className="max-w-72 px-3 py-2.5 font-medium [overflow-wrap:anywhere]">{conexao.nome}</td>
                    <td className="px-3 py-2.5">{rotulosTipo[conexao.tipo] ?? conexao.tipo}</td>
                    <td className="px-3 py-2.5">
                      <Badge variant={ativa ? "secondary" : "outline"}>{ativa ? "Ativa" : "Desativada"}</Badge>
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-muted-foreground">
                      {conexao.segredo_definido ? conexao.segredo_mascara : "Sem chave"}
                    </td>
                    <td className="px-3 py-2.5 text-right" onClick={acao} onKeyDown={(e) => e.stopPropagation()}>
                      <div className="flex justify-end gap-1">
                        <Button type="button" variant="ghost" size="xs" aria-label={`Editar ${conexao.nome}`} onClick={() => onEditar?.(conexao)}>
                          Editar
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="xs"
                          aria-label={`${ativa ? "Desativar" : "Reativar"} ${conexao.nome}`}
                          onClick={() => onAlternarSituacao?.(conexao)}
                        >
                          {ativa ? "Desativar" : "Reativar"}
                        </Button>
                        <Button type="button" variant="ghost" size="xs" aria-label={`Excluir ${conexao.nome}`} onClick={() => onExcluir?.(conexao)}>
                          Excluir
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
