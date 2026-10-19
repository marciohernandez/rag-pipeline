"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import EntradaEnderecos from "@/features/conversao/EntradaEnderecos";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { LoteConversaoResumo } from "@/features/conversao/DataGridLotesConversao";
import PainelLoteConversao from "@/features/conversao/PainelLoteConversao";
import { apiJson } from "@/lib/api-client";

/**
 * Formulário de envio multi-formato e painel de acompanhamento pós-envio
 * (SPEC-0023, US-001). Modelado em `UploadBaseSheet`: os limites do backend
 * (`src/app/routers/conversao.py`) são espelhados aqui e checados antes de
 * qualquer chamada — nenhum lote parcial é criado quando o envio é inválido.
 *
 * Depois do envio (201), o painel de acompanhamento (`PainelLoteConversao`)
 * substitui o formulário dentro do mesmo `Sheet`, mostrando a lista de
 * documentos com polling automático até todos chegarem a um estado terminal.
 */

const MAX_ARQUIVOS = 50;
const MAX_BYTES_ARQUIVO = 40 * 1024 * 1024;
const MAX_BYTES_TOTAL = 50 * 1024 * 1024;
const EXTENSOES_ACEITAS = [
  "html",
  "pdf",
  "ppt",
  "pptx",
  "doc",
  "docx",
  "xls",
  "xlsx",
  "jpg",
  "jpeg",
  "png",
];
const ACCEPT = EXTENSOES_ACEITAS.map((extensao) => `.${extensao}`).join(",");

interface ConversaoSheetProps {
  open: boolean;
  workspaceId: string;
  papel?: string;
  onOpenChange?: (open: boolean) => void;
  onCriado?: (lote: LoteConversaoResumo) => void;
}

function extensao(nome: string): string {
  const partes = nome.toLowerCase().split(".");
  return partes.length > 1 ? (partes.pop() ?? "") : "";
}

function formatarBytes(bytes: number): string {
  if (bytes < 1024 * 1024) return `${bytes} bytes`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validar(arquivos: File[], maxArquivos: number): string | null {
  if (arquivos.length === 0) {
    return "Selecione ao menos um arquivo.";
  }
  if (arquivos.length > maxArquivos) {
    return `Limite de ${maxArquivos} arquivos por lote.`;
  }
  const invalido = arquivos.find((arquivo) => !EXTENSOES_ACEITAS.includes(extensao(arquivo.name)));
  if (invalido) {
    return `Extensão não suportada: ${invalido.name}.`;
  }
  return null;
}

export default function ConversaoSheet({
  open,
  workspaceId,
  papel,
  onOpenChange,
  onCriado,
}: ConversaoSheetProps) {
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [urls, setUrls] = useState<string[]>([]);
  const [recusados, setRecusados] = useState<{nome_arquivo: string; motivo: string}[]>([]);
  const [limites, setLimites] = useState({ max_arquivos: MAX_ARQUIVOS, max_bytes_arquivo: MAX_BYTES_ARQUIVO, max_bytes_lote: MAX_BYTES_TOTAL });
  useEffect(() => {
    if (!open) return;
    let cancelado = false;
    apiJson<typeof limites>("/api/v1/conversoes/limites").then((dados) => { if (!cancelado && typeof dados.max_bytes_arquivo === "number") setLimites(dados); }).catch(() => { if (!cancelado) setErro("Não foi possível carregar os limites; tente novamente."); });
    return () => { cancelado = true; };
  }, [open]);
  const [enviando, setEnviando] = useState(false);
  const [lote, setLote] = useState<LoteConversaoResumo | null>(null);

  useEffect(() => {
    if (lote) onCriado?.(lote);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lote]);

  function aoSelecionar(lista: FileList | null) {
    setErro(null);
    setArquivos(lista ? Array.from(lista) : []);
  }

  function remover(nome: string) {
    setArquivos((atual) => atual.filter((arquivo) => arquivo.name !== nome));
  }

  async function converter() {
    const problema = arquivos.length ? validar(arquivos, limites.max_arquivos) : (urls.length ? null : "Informe ao menos um documento ou endereço.");
    if (problema) {
      setErro(problema);
      return;
    }
    const corpo = new FormData();
    for (const arquivo of arquivos) {
      corpo.append("arquivos", arquivo, arquivo.name);
    }
    corpo.set("workspace_id", workspaceId);
    corpo.set(
      "metadados",
      JSON.stringify(
        arquivos.map((arquivo) => ({
          nome: arquivo.name,
          modificado_em: arquivo.lastModified,
          pasta: (arquivo.webkitRelativePath || "").split("/").slice(0, -1).join("/") || null,
        })),
      ),
    );
    urls.forEach((url) => corpo.append("urls", url));

    setEnviando(true);
    setErro(null);
    try {
      const criado = await apiJson<LoteConversaoResumo & {recusados?: {nome_arquivo: string; motivo: string}[]}>("/api/v1/conversoes", {
        method: "POST",
        body: corpo,
      });
      setArquivos([]);
      setUrls([]);
      setRecusados(criado.recusados ?? []);
      setLote(criado);
    } catch (causa) {
      setErro(causa && typeof causa === "object" && "detail" in causa && typeof causa.detail === "string" ? causa.detail : "Não foi possível converter os documentos. Tente novamente.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Converter documentos</SheetTitle>
          <SheetDescription>
            Envie PDF, Word, PowerPoint, Excel, HTML, imagem ou endereço público para converter em Markdown.
          </SheetDescription>
        </SheetHeader>

        {recusados.length > 0 && <Alert variant="destructive" className="mx-4 w-auto"><AlertDescription><ul>{recusados.map((item, i) => <li key={i}>{item.nome_arquivo}: {item.motivo}</li>)}</ul></AlertDescription></Alert>}
        {lote ? (
          <div className="px-4">
            <PainelLoteConversao lote={lote} papel={papel} onAtualizado={setLote} />
          </div>
        ) : (
          <>
            <Tabs defaultValue="arquivos" className="px-4">
            <TabsList className="h-auto max-w-full flex-wrap"><TabsTrigger value="arquivos">Arquivos</TabsTrigger><TabsTrigger value="endereco">Endereço</TabsTrigger></TabsList>
            <TabsContent value="endereco"><EntradaEnderecos disabled={enviando} onAdicionar={(url) => setUrls((atual) => [...atual, url])} /></TabsContent>
            <TabsContent value="arquivos">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="conversao-arquivos">Documentos</Label>
              <input
                id="conversao-arquivos"
                type="file"
                multiple
                accept={ACCEPT}
                onChange={(evento) => aoSelecionar(evento.target.files)}
                disabled={enviando}
                className="text-sm file:mr-2 file:rounded-md file:border file:border-input file:bg-background file:px-2 file:py-1 file:text-sm"
              />
              <p className="text-xs text-muted-foreground">
                PDF, Office, HTML e imagens — até {formatarBytes(limites.max_bytes_arquivo)} por arquivo, {formatarBytes(limites.max_bytes_lote)} por lote e {limites.max_arquivos} documentos. Apenas o excedente será recusado.
              </p>
            </div>

            </TabsContent></Tabs>
            {urls.length > 0 && <ul className="flex flex-col gap-2 px-4 text-sm">{urls.map((url, i) => <li key={`${i}-${url}`} className="flex min-w-0 items-center gap-2"><span className="min-w-0 flex-1 [overflow-wrap:anywhere]">{url}</span><Button variant="ghost" size="xs" onClick={() => setUrls((atual) => atual.filter((_, j) => j !== i))} disabled={enviando}>Remover endereço {i + 1}</Button></li>)}</ul>}
            {arquivos.length > 0 ? (
              <ul className="flex flex-col gap-1 px-4 text-sm">
                {arquivos.map((arquivo) => (
                  <li key={arquivo.name} className="flex items-center justify-between gap-2">
                    <span className="truncate font-mono text-xs">
                      {arquivo.name} ({formatarBytes(arquivo.size)})
                    </span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="xs"
                      onClick={() => remover(arquivo.name)}
                      disabled={enviando}
                    >
                      Remover
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}

            {erro ? (
              <Alert variant="destructive" className="mx-4 w-auto">
                <AlertDescription>{erro}</AlertDescription>
              </Alert>
            ) : null}

            <SheetFooter className="sm:flex-row sm:justify-end">
              <Button
                type="button"
                onClick={converter}
                disabled={enviando || (arquivos.length === 0 && urls.length === 0)}
                className="w-full sm:w-auto"
              >
                {enviando ? "Convertendo…" : "Converter"}
              </Button>
            </SheetFooter>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
