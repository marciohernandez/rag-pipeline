"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
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
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function validar(arquivos: File[]): string | null {
  if (arquivos.length === 0) {
    return "Selecione ao menos um arquivo.";
  }
  if (arquivos.length > MAX_ARQUIVOS) {
    return `Limite de ${MAX_ARQUIVOS} arquivos por lote.`;
  }
  const invalido = arquivos.find((arquivo) => !EXTENSOES_ACEITAS.includes(extensao(arquivo.name)));
  if (invalido) {
    return `Extensão não suportada: ${invalido.name}.`;
  }
  const grande = arquivos.find((arquivo) => arquivo.size > MAX_BYTES_ARQUIVO);
  if (grande) {
    return `O arquivo ${grande.name} passa de 40 MB.`;
  }
  const total = arquivos.reduce((soma, arquivo) => soma + arquivo.size, 0);
  if (total > MAX_BYTES_TOTAL) {
    return "O envio passa de 50 MB no total.";
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
    const problema = validar(arquivos);
    if (problema) {
      setErro(problema);
      return;
    }
    const corpo = new FormData();
    for (const arquivo of arquivos) {
      corpo.append("arquivos", arquivo, arquivo.name);
    }
    corpo.set("workspace_id", workspaceId);

    setEnviando(true);
    setErro(null);
    try {
      const criado = await apiJson<LoteConversaoResumo>("/api/v1/conversoes", {
        method: "POST",
        body: corpo,
      });
      setArquivos([]);
      setLote(criado);
    } catch {
      setErro("Não foi possível converter os documentos. Tente novamente.");
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
            Envie PDF, Word, PowerPoint, Excel ou imagem para converter em Markdown.
          </SheetDescription>
        </SheetHeader>

        {lote ? (
          <div className="px-4">
            <PainelLoteConversao lote={lote} papel={papel} onAtualizado={setLote} />
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-1.5 px-4">
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
                PDF, PPT/PPTX, DOC/DOCX, XLS/XLSX, JPG/JPEG/PNG — até 40 MB por arquivo, 50 MB no
                total e 50 arquivos por lote.
              </p>
            </div>

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
                disabled={enviando || arquivos.length === 0}
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
