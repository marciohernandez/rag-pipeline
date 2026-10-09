"use client";

import { useEffect, useRef, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { seletor } from "@/features/ingestao/seletor";
import {
  CAMPOS_POR_ESTRATEGIA,
  ENCODINGS,
  PROCESSAMENTO_PADRAO,
  nivelEfetivo,
  rotulosSplitter,
  validarDivisao,
  type Padroes,
  type Processamento,
} from "@/lib/ingestao";

interface Props {
  arquivos: File[];
  padroes: Padroes;
  splitter: string;
  tamanho: string;
  overlap: string;
  /** Incrementa a cada tentativa de avançar; mostra os erros e foca o primeiro. */
  tentativas: number;
  onAlterar: (campo: "splitter" | "tamanho" | "overlap", valor: string) => void;
  /** Escolhas além da divisão básica (SPEC-0029); ausentes, valem os padrões. */
  processamento?: Processamento;
  onAlterarProcessamento?: <G extends keyof Processamento>(
    grupo: G,
    campo: keyof Processamento[G],
    valor: Processamento[G][keyof Processamento[G]],
  ) => void;
}

const NIVEIS = [1, 2, 3, 4, 5, 6];
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
 * Etapa Divisão (SPEC-0026 e SPEC-0029): estratégia de divisão com os campos
 * próprios de cada uma, resumos de seção, Dividir por cabeçalhos e o bloco
 * Qualidade. Os arquivos com configuração própria no frontmatter são avisados.
 */
export default function EtapaDivisao({
  arquivos,
  padroes,
  splitter,
  tamanho,
  overlap,
  tentativas,
  onAlterar,
  processamento = PROCESSAMENTO_PADRAO,
  onAlterarProcessamento = () => {},
}: Props) {
  const campoTamanho = useRef<HTMLInputElement>(null);
  const campoOverlap = useRef<HTMLInputElement>(null);
  const [tocados, setTocados] = useState<{ tamanho: boolean; overlap: boolean }>({ tamanho: false, overlap: false });
  const [qualidadeAberta, setQualidadeAberta] = useState(false);
  const [novoStatus, setNovoStatus] = useState("");
  const erros = validarDivisao(tamanho, overlap, padroes.limites, splitter, processamento);
  const proprios = useArquivosComConfiguracaoPropria(arquivos);
  const mostrar = (campo: "tamanho" | "overlap") => (tentativas > 0 || tocados[campo]) && erros[campo];
  const campos = CAMPOS_POR_ESTRATEGIA[splitter] ?? ["tamanho", "overlap"];
  const usa = (campo: string) => campos.includes(campo);
  const tokens = splitter === "token";
  const limitesTamanho = tokens ? (padroes.limites.token_size ?? { min: 50, max: 2000 }) : padroes.limites.chunk_size;
  const status = processamento.contrato.status_bloqueado;

  useEffect(() => {
    if (tentativas === 0) return;
    if (erros.tamanho) campoTamanho.current?.focus();
    else if (erros.overlap) campoOverlap.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só reage a uma nova tentativa
  }, [tentativas]);

  function adicionarStatus() {
    const valor = novoStatus.trim();
    if (!valor || status.includes(valor) || valor.length > 40 || status.length >= 20) return;
    onAlterarProcessamento("contrato", "status_bloqueado", [...status, valor]);
    setNovoStatus("");
  }

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
          Estratégias do LangChain para Markdown. Cada uma mostra só os campos que usa.
        </p>
      </div>
      {usa("tamanho") ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="divisao-tamanho">{tokens ? "Tamanho do chunk (tokens)" : "Tamanho do chunk"}</Label>
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
            {tokens ? "Tokens" : "Caracteres"} por chunk, de {limitesTamanho.min} a {limitesTamanho.max}.
          </p>
          {mostrar("tamanho") ? <p role="alert" className="text-sm text-destructive">{erros.tamanho}</p> : null}
        </div>
      ) : null}
      {usa("overlap") ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="divisao-overlap">{tokens ? "Overlap (tokens)" : "Overlap"}</Label>
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
            {tokens ? "Tokens" : "Caracteres"} repetidos entre chunks seguidos, até a metade do tamanho.
          </p>
          {mostrar("overlap") ? <p role="alert" className="text-sm text-destructive">{erros.overlap}</p> : null}
        </div>
      ) : null}
      {usa("separador") ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="divisao-separador">Separador</Label>
          <Input
            id="divisao-separador"
            value={processamento.opcoes.separador}
            maxLength={10}
            onChange={(e) => onAlterarProcessamento("opcoes", "separador", e.target.value)}
            aria-invalid={erros.separador ? "true" : undefined}
            aria-describedby="ajuda-divisao-separador"
          />
          <p id="ajuda-divisao-separador" className="text-xs text-muted-foreground">
            Texto onde o chunk pode ser cortado. Use \n para quebra de linha e \t para tabulação.
          </p>
          {erros.separador ? <p role="alert" className="text-sm text-destructive">{erros.separador}</p> : null}
        </div>
      ) : null}
      {usa("encoding") ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="divisao-encoding">Encoding</Label>
          <select
            id="divisao-encoding"
            value={processamento.opcoes.encoding}
            onChange={(e) => onAlterarProcessamento("opcoes", "encoding", e.target.value)}
            className={seletor}
          >
            {ENCODINGS.map((valor) => (
              <option key={valor} value={valor}>
                {valor}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">Tokenizador usado para contar o tamanho do chunk.</p>
        </div>
      ) : null}
      {usa("nivel_cabecalho") ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="divisao-nivel">Dividir por cabeçalhos</Label>
          <select
            id="divisao-nivel"
            value={nivelEfetivo(splitter, processamento)}
            onChange={(e) => onAlterarProcessamento("opcoes", "nivel_cabecalho", Number(e.target.value))}
            className={seletor}
          >
            {splitter === "markdown" ? <option value={0}>Desativado</option> : null}
            {NIVEIS.map((nivel) => (
              <option key={nivel} value={nivel}>
                {`Até H${nivel}`}
              </option>
            ))}
          </select>
          <p className="text-xs text-muted-foreground">Divide nos títulos até o nível escolhido antes de aplicar o tamanho.</p>
        </div>
      ) : null}
      {usa("remover_cabecalhos") ? (
        <div className="flex items-center gap-2">
          <input
            id="divisao-remover"
            type="checkbox"
            className="size-4 accent-primary"
            checked={processamento.opcoes.remover_cabecalhos}
            onChange={(e) => onAlterarProcessamento("opcoes", "remover_cabecalhos", e.target.checked)}
          />
          <Label htmlFor="divisao-remover">Remover cabeçalhos do texto</Label>
        </div>
      ) : null}
      {usa("resumos") ? (
        <fieldset className="flex flex-col gap-3 rounded-lg border p-3 md:col-span-2">
          <legend className="px-1 text-sm font-medium">Resumos de seção</legend>
          <div className="flex items-center gap-2">
            <input
              id="divisao-resumos"
              type="checkbox"
              className="size-4 accent-primary"
              checked={processamento.resumos.ativo}
              onChange={(e) => onAlterarProcessamento("resumos", "ativo", e.target.checked)}
            />
            <Label htmlFor="divisao-resumos">Gerar um chunk-resumo para seções com várias subseções</Label>
          </div>
          {processamento.resumos.ativo ? (
            <div className="flex max-w-xs flex-col gap-1.5">
              <Label htmlFor="divisao-subsecoes">Mínimo de subseções</Label>
              <Input
                id="divisao-subsecoes"
                type="number"
                min={2}
                max={10}
                value={processamento.resumos.minimo_subsecoes}
                onChange={(e) => onAlterarProcessamento("resumos", "minimo_subsecoes", Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground">De 2 a 10 subseções.</p>
            </div>
          ) : null}
        </fieldset>
      ) : null}
      <div className="flex flex-col gap-3 rounded-lg border p-3 md:col-span-2">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="self-start"
          aria-expanded={qualidadeAberta}
          aria-controls="divisao-qualidade"
          onClick={() => setQualidadeAberta((aberta) => !aberta)}
        >
          {qualidadeAberta ? "Ocultar Qualidade" : "Qualidade"}
        </Button>
        {qualidadeAberta ? (
          <div id="divisao-qualidade" className="grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="divisao-minimo-util">Mínimo útil</Label>
              <Input
                id="divisao-minimo-util"
                type="number"
                min={0}
                max={1000}
                value={processamento.qualidade.minimo_util}
                onChange={(e) => onAlterarProcessamento("qualidade", "minimo_util", Number(e.target.value))}
              />
              <p className="text-xs text-muted-foreground">Chunks com menos caracteres úteis só geram aviso na Prévia.</p>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="divisao-status">Status bloqueados</Label>
              <div className="flex gap-2">
                <Input
                  id="divisao-status"
                  value={novoStatus}
                  maxLength={40}
                  onChange={(e) => setNovoStatus(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      adicionarStatus();
                    }
                  }}
                />
                <Button type="button" variant="outline" size="sm" onClick={adicionarStatus}>
                  Adicionar
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Documentos com este `status` no frontmatter ficam fora da indexação. Até 20.
              </p>
              {status.length > 0 ? (
                <ul className="flex flex-wrap gap-2" aria-label="Status bloqueados">
                  {status.map((valor) => (
                    <li key={valor} className="flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs">
                      {valor}
                      <button
                        type="button"
                        className="text-muted-foreground hover:text-foreground"
                        aria-label={`Remover ${valor}`}
                        onClick={() =>
                          onAlterarProcessamento(
                            "contrato",
                            "status_bloqueado",
                            status.filter((item) => item !== valor),
                          )
                        }
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          </div>
        ) : null}
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
