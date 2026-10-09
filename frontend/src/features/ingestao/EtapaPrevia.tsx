"use client";

import { useEffect, useState } from "react";

import { IndicadorProcessamento } from "@/components/IndicadorProcessamento";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { TAMANHO_PAGINA, type Previa } from "@/features/ingestao/useFluxoIngestao";
import { seletor } from "@/features/ingestao/seletor";

interface Props {
  previa: Previa | null;
  calculando: boolean;
  erro: string | null;
  documento: string | null;
  /** Nomes dos arquivos enviados, para o filtro por documento. */
  documentos: string[];
  onCalcular: (pagina?: number, documento?: string | null) => Promise<void> | void;
  /** Chunks por página escolhidos na barra da Prévia (SPEC-0029). */
  tamanhoPagina?: number;
}

const LIMITE_TEXTO = 240;

/**
 * Etapa Prévia (SPEC-0026): resumo, avisos e lista paginada e somente leitura
 * dos chunks. Ajustar significa voltar à Divisão; nada é editado nem gravado.
 */
export default function EtapaPrevia({
  previa,
  calculando,
  erro,
  documento,
  documentos,
  onCalcular,
  tamanhoPagina = TAMANHO_PAGINA,
}: Props) {
  const [abertos, setAbertos] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (previa === null && !calculando && !erro) void onCalcular(1, null);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- calcula uma vez ao entrar na etapa
  }, [previa]);

  if (erro) {
    return (
      <Alert variant="destructive">
        <AlertDescription className="flex flex-wrap items-center justify-between gap-3">
          <span>{erro}</span>
          <Button type="button" variant="outline" size="sm" onClick={() => void onCalcular(1, documento)}>
            Tentar novamente
          </Button>
        </AlertDescription>
      </Alert>
    );
  }
  if (previa === null) {
    return <IndicadorProcessamento>Calculando a prévia dos chunks</IndicadorProcessamento>;
  }

  const paginaAtual = previa.pagina;
  const ultima = Math.max(1, Math.ceil(previa.total / tamanhoPagina));
  const alternar = (chave: string) =>
    setAbertos((atuais) => {
      const novo = new Set(atuais);
      if (!novo.delete(chave)) novo.add(chave);
      return novo;
    });

  return (
    <div className="flex flex-col gap-4">
      {calculando ? <IndicadorProcessamento>Atualizando a prévia</IndicadorProcessamento> : null}
      <p role="status" className="sr-only">
        Prévia calculada: {previa.resumo.chunks} chunks em {previa.resumo.documentos} documentos.
      </p>
      <dl className="grid grid-cols-3 gap-px overflow-hidden rounded-lg border bg-border text-sm">
        {[
          ["Documentos", previa.resumo.documentos],
          ["Chunks", previa.resumo.chunks],
          ["Tamanho médio", `${previa.resumo.tamanho_medio} caracteres`],
        ].map(([rotulo, valor]) => (
          <div key={String(rotulo)} className="flex flex-col gap-1 bg-background p-3">
            <dt className="text-muted-foreground">{rotulo}</dt>
            <dd className="text-base font-medium">{valor}</dd>
          </div>
        ))}
      </dl>
      {previa.avisos.map((aviso) => (
        <Alert key={aviso}>
          <AlertDescription>{aviso}</AlertDescription>
        </Alert>
      ))}
      {documentos.length > 1 ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="previa-documento">Filtrar por documento</Label>
          <select
            id="previa-documento"
            value={documento ?? ""}
            onChange={(e) => void onCalcular(1, e.target.value || null)}
            className={seletor}
          >
            <option value="">Todos os documentos</option>
            {documentos.map((nome) => (
              <option key={nome} value={nome}>
                {nome}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      <ol className="flex flex-col overflow-hidden rounded-lg border text-sm" aria-label="Chunks da prévia">
        {previa.chunks.map((chunk) => {
          const chave = `${chunk.documento}-${chunk.posicao}-${chunk.tipo ?? "detail"}`;
          const longo = chunk.texto.length > LIMITE_TEXTO;
          const aberto = abertos.has(chave);
          return (
            <li key={chave} className="flex flex-col gap-1.5 border-b p-3 last:border-b-0">
              <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                <span className="font-medium text-foreground [overflow-wrap:anywhere]">{chunk.documento}</span>
                <span>posição {chunk.posicao}</span>
                <span>{chunk.tamanho} caracteres</span>
                {chunk.tipo === "summary" ? <Badge variant="outline">Resumo de seção</Badge> : null}
              </div>
              <p className="whitespace-pre-wrap [overflow-wrap:anywhere]">
                {longo && !aberto ? `${chunk.texto.slice(0, LIMITE_TEXTO)}…` : chunk.texto}
              </p>
              {longo ? (
                <Button type="button" variant="link" size="xs" className="w-fit px-0" aria-expanded={aberto} onClick={() => alternar(chave)}>
                  {aberto ? "ver menos" : "ver mais"}
                </Button>
              ) : null}
            </li>
          );
        })}
        {previa.chunks.length === 0 ? <li className="p-6 text-center text-muted-foreground">Nenhum chunk para exibir.</li> : null}
      </ol>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="text-muted-foreground">
          Página {paginaAtual} de {ultima}
        </span>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" disabled={paginaAtual <= 1 || calculando} onClick={() => void onCalcular(paginaAtual - 1, documento)}>
            Página anterior
          </Button>
          <Button type="button" variant="outline" size="sm" disabled={paginaAtual >= ultima || calculando} onClick={() => void onCalcular(paginaAtual + 1, documento)}>
            Página seguinte
          </Button>
        </div>
      </div>
    </div>
  );
}
