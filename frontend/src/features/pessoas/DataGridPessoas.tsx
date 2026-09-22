"use client";

import type { KeyboardEvent, MouseEvent } from "react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export interface PessoaResumo {
  id: string;
  nome: string;
  email: string;
  papel: string;
  situacao: string;
  precisa_trocar_senha: boolean;
  criada_em?: string;
  criada_por?: { id: string; nome: string; desativada: boolean } | null;
}

interface Props {
  pessoas: PessoaResumo[];
  carregando?: boolean;
  onEditar?: (pessoa: PessoaResumo) => void;
  onAlternarSituacao?: (pessoa: PessoaResumo) => void;
}

export default function DataGridPessoas({ pessoas, carregando = false, onEditar, onAlternarSituacao }: Props) {
  const router = useRouter();
  function abrir(id: string) { router.push(`/pessoas/${id}`); }
  function tecla(evento: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (evento.key === "Enter" || evento.key === " ") { evento.preventDefault(); abrir(id); }
  }
  function acao(evento: MouseEvent) { evento.stopPropagation(); }

  return (
    <div className="w-full overflow-x-auto rounded-lg border">
      <table className="w-full min-w-[58rem] border-collapse text-sm" aria-busy={carregando}>
        <caption className="sr-only">Pessoas da equipe ativa</caption>
        <thead><tr className="border-b bg-muted/40 text-left">{["ID", "Nome", "E-mail", "Papel", "Situação"].map((nome) => <th key={nome} scope="col" className="px-3 py-2 font-medium text-muted-foreground">{nome}</th>)}<th scope="col"><span className="sr-only">Ações</span></th></tr></thead>
        <tbody>
          {carregando ? Array.from({ length: 3 }).map((_, i) => <tr key={i} className="border-b">{Array.from({ length: 6 }).map((__, j) => <td key={j} className="px-3 py-2.5"><Skeleton className="h-4 w-24" /></td>)}</tr>) : pessoas.length === 0 ? (
            <tr><td colSpan={6} className="px-3 py-10 text-center text-muted-foreground">Nenhuma pessoa encontrada.</td></tr>
          ) : pessoas.map((pessoa) => {
            const ativa = pessoa.situacao === "ativa";
            return <tr key={pessoa.id} tabIndex={0} aria-label={`Pessoa ${pessoa.nome}`} onClick={() => abrir(pessoa.id)} onKeyDown={(e) => tecla(e, pessoa.id)} className="cursor-pointer border-b outline-none last:border-0 hover:bg-muted/40 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring">
              <td className="px-3 py-2.5 font-mono text-xs">{pessoa.id}</td><td className="px-3 py-2.5 font-medium">{pessoa.nome}</td><td className="max-w-72 px-3 py-2.5 [overflow-wrap:anywhere]">{pessoa.email}</td><td className="px-3 py-2.5">{pessoa.papel}</td><td className="px-3 py-2.5"><Badge variant={ativa ? "secondary" : "outline"}>{ativa ? "Ativa" : "Desativada"}</Badge></td>
              <td className="px-3 py-2.5 text-right" onClick={acao} onKeyDown={(e) => e.stopPropagation()}><div className="flex justify-end gap-1"><Button type="button" variant="ghost" size="xs" aria-label={`Editar ${pessoa.nome}`} onClick={() => onEditar?.(pessoa)}>Editar</Button><Button type="button" variant="ghost" size="xs" aria-label={`${ativa ? "Desativar" : "Reativar"} ${pessoa.nome}`} onClick={() => onAlternarSituacao?.(pessoa)}>{ativa ? "Desativar" : "Reativar"}</Button></div></td>
            </tr>;
          })}
        </tbody>
      </table>
    </div>
  );
}
