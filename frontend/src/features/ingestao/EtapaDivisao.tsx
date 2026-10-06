"use client";

import { useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { rotulosSplitter, validarDivisao, type Padroes } from "@/lib/ingestao";

interface Props {
  arquivos: File[];
  padroes: Padroes;
  splitter: string;
  tamanho: string;
  overlap: string;
  /** Incrementa a cada tentativa de avançar; mostra os erros e foca o primeiro. */
  tentativas: number;
  onAlterar: (campo: "splitter" | "tamanho" | "overlap", valor: string) => void;
}

const seletor =
  "h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";
const CHAVES_PROPRIAS = /^(splitter|chunk_size_recommended|chunk_overlap_recommended)\s*:/m;

function lerInicio(arquivo: File): Promise<string> {
  return new Promise((resolver) => {
    const leitor = new FileReader();
    leitor.onload = () => resolver(String(leitor.result ?? ""));
    leitor.onerror = () => resolver("");
    leitor.readAsText(arquivo.slice(0, 2048));
  });
}

/** Arquivos cujo frontmatter traz configuração própria e, portanto, ignora o formulário. */
function useArquivosComConfiguracaoPropria(arquivos: File[]) {
  const [nomes, setNomes] = useState<string[]>([]);
  useEffect(() => {
    let ativo = true;
    void Promise.all(
      arquivos.map(async (arquivo) => {
        const inicio = await lerInicio(arquivo);
        const frontmatter = inicio.match(/^---\s*\n([\s\S]*?)\n---/)?.[1] ?? "";
        return CHAVES_PROPRIAS.test(frontmatter) ? arquivo.name : null;
      }),
    ).then((encontrados) => {
      if (ativo) setNomes(encontrados.filter((n): n is string => n !== null));
    });
    return () => {
      ativo = false;
    };
  }, [arquivos]);
  return nomes;
}

/**
 * Etapa Divisão (SPEC-0026): splitter, tamanho e overlap pré-preenchidos com os
 * padrões do backend. Sem seção avançada nem configuração por arquivo; os
 * arquivos com configuração própria no frontmatter só são avisados.
 */
export default function EtapaDivisao({ arquivos, padroes, splitter, tamanho, overlap, tentativas, onAlterar }: Props) {
  const campoTamanho = useRef<HTMLInputElement>(null);
  const campoOverlap = useRef<HTMLInputElement>(null);
  const [tocados, setTocados] = useState<{ tamanho: boolean; overlap: boolean }>({ tamanho: false, overlap: false });
  const erros = validarDivisao(tamanho, overlap, padroes.limites);
  const proprios = useArquivosComConfiguracaoPropria(arquivos);
  const mostrar = (campo: "tamanho" | "overlap") => (tentativas > 0 || tocados[campo]) && erros[campo];

  useEffect(() => {
    if (tentativas === 0) return;
    if (erros.tamanho) campoTamanho.current?.focus();
    else if (erros.overlap) campoOverlap.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só reage a uma nova tentativa
  }, [tentativas]);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="flex flex-col gap-1.5 md:col-span-2">
        <Label htmlFor="divisao-splitter">Estratégia de divisão</Label>
        <select id="divisao-splitter" value={splitter} onChange={(e) => onAlterar("splitter", e.target.value)} className={seletor}>
          {padroes.splitters.map((valor) => (
            <option key={valor} value={valor}>
              {rotulosSplitter[valor] ?? valor}
            </option>
          ))}
        </select>
        <p className="text-xs text-muted-foreground">
          Cabeçalhos respeita os títulos do Markdown; recursivo divide por parágrafos, linhas e caracteres.
        </p>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="divisao-tamanho">Tamanho do chunk</Label>
        <Input
          ref={campoTamanho}
          id="divisao-tamanho"
          type="number"
          value={tamanho}
          onChange={(e) => onAlterar("tamanho", e.target.value)}
          onBlur={() => setTocados((t) => ({ ...t, tamanho: true }))}
          aria-invalid={mostrar("tamanho") ? "true" : undefined}
          aria-describedby="ajuda-divisao-tamanho"
        />
        <p id="ajuda-divisao-tamanho" className="text-xs text-muted-foreground">
          Caracteres por chunk, de {padroes.limites.chunk_size.min} a {padroes.limites.chunk_size.max}.
        </p>
        {mostrar("tamanho") ? <p role="alert" className="text-sm text-destructive">{erros.tamanho}</p> : null}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="divisao-overlap">Overlap</Label>
        <Input
          ref={campoOverlap}
          id="divisao-overlap"
          type="number"
          value={overlap}
          onChange={(e) => onAlterar("overlap", e.target.value)}
          onBlur={() => setTocados((t) => ({ ...t, overlap: true }))}
          aria-invalid={mostrar("overlap") ? "true" : undefined}
          aria-describedby="ajuda-divisao-overlap"
        />
        <p id="ajuda-divisao-overlap" className="text-xs text-muted-foreground">
          Caracteres repetidos entre chunks seguidos, até a metade do tamanho.
        </p>
        {mostrar("overlap") ? <p role="alert" className="text-sm text-destructive">{erros.overlap}</p> : null}
      </div>
      {proprios.length > 0 ? (
        <Alert className="md:col-span-2">
          <AlertDescription>
            Estes arquivos têm configuração própria no frontmatter e ignoram o formulário (inclusive os Q&amp;A): {proprios.join(", ")}.
          </AlertDescription>
        </Alert>
      ) : null}
    </div>
  );
}
