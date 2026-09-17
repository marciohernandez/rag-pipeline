"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

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
import { ApiError, apiJson } from "@/lib/api-client";

/**
 * Envio de base pela tela Projeto (SPEC-0013, US-002 / AC-006 / AC-007).
 *
 * `Sheet` contextual com upload múltiplo de `.md` e a contingência "base
 * preparada". Os limites do backend (`src/app/routers/bases.py`) são
 * espelhados aqui e checados antes de qualquer chamada — nenhuma base
 * parcial é criada quando o envio é inválido.
 *
 * Criar a base não a processa: quem processa é a execução agendada por
 * `POST /bases/{id}/executions` (FR-009). Até a Fase 12 nenhuma tela chamava
 * esse endpoint, e toda base enviada ficava parada sem execução.
 */

const MAX_ARQUIVOS = 50;
const MAX_BYTES_ARQUIVO = 5 * 1024 * 1024;
const MAX_BYTES_TOTAL = 50 * 1024 * 1024;

interface UploadBaseSheetProps {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  onCreated: (baseId?: string) => void;
}

function validar(arquivos: File[]): string | null {
  if (arquivos.length === 0) {
    return "Selecione ao menos um arquivo .md.";
  }
  if (arquivos.length > MAX_ARQUIVOS) {
    return `Limite de ${MAX_ARQUIVOS} arquivos por envio.`;
  }
  const semExtensao = arquivos.filter(
    (arquivo) => !arquivo.name.toLowerCase().endsWith(".md"),
  );
  if (semExtensao.length > 0) {
    return `Só arquivos .md são aceitos: ${semExtensao
      .map((arquivo) => arquivo.name)
      .join(", ")}.`;
  }
  const grande = arquivos.find((arquivo) => arquivo.size > MAX_BYTES_ARQUIVO);
  if (grande) {
    return `O arquivo ${grande.name} passa de 5 MB.`;
  }
  const total = arquivos.reduce((soma, arquivo) => soma + arquivo.size, 0);
  if (total > MAX_BYTES_TOTAL) {
    return "O envio passa de 50 MB no total.";
  }
  return null;
}

export default function UploadBaseSheet({
  open,
  onOpenChange,
  onCreated,
}: UploadBaseSheetProps) {
  const router = useRouter();
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  function aoSelecionar(lista: FileList | null) {
    setErro(null);
    setArquivos(lista ? Array.from(lista) : []);
  }

  function remover(nome: string) {
    setArquivos((atual) => atual.filter((arquivo) => arquivo.name !== nome));
  }

  async function agendarEAbrir(baseId: string) {
    try {
      await apiJson(`/api/v1/bases/${baseId}/executions`, { method: "POST" });
    } catch (causa) {
      // 409 é a execução ativa que o backend já tem para esta base: o destino
      // continua sendo o detalhe dela, sem erro para a pessoa (AC-024).
      if (!(causa instanceof ApiError && causa.status === 409)) {
        setErro(
          "A base foi enviada, mas o processamento não começou. Abra a base para tentar de novo.",
        );
        return;
      }
    }
    router.push(`/execucoes/${baseId}`);
  }

  async function criar(
    body: FormData | URLSearchParams,
    mensagemDeFalha: string,
  ) {
    setEnviando(true);
    setErro(null);
    try {
      const resposta = await apiJson<{ base_id: string }>("/api/v1/bases", {
        method: "POST",
        body,
      });
      setArquivos([]);
      onCreated(resposta.base_id);
      await agendarEAbrir(resposta.base_id);
    } catch {
      setErro(mensagemDeFalha);
    } finally {
      setEnviando(false);
    }
  }

  function enviarUpload() {
    const problema = validar(arquivos);
    if (problema) {
      setErro(problema);
      return;
    }
    const corpo = new FormData();
    for (const arquivo of arquivos) {
      corpo.append("arquivos", arquivo, arquivo.name);
    }
    void criar(corpo, "Não foi possível enviar a base. Tente novamente.");
  }

  function usarBasePreparada() {
    void criar(
      new URLSearchParams({ usar_base_preparada: "true" }),
      "Não foi possível usar a base preparada. Tente novamente.",
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Enviar base</SheetTitle>
          <SheetDescription>
            Envie arquivos Markdown (.md) ou use a base preparada de
            demonstração.
          </SheetDescription>
        </SheetHeader>

        <div className="flex flex-col gap-1.5 px-4">
          <Label htmlFor="arquivos">Arquivos Markdown</Label>
          <input
            id="arquivos"
            type="file"
            multiple
            accept=".md"
            onChange={(evento) => aoSelecionar(evento.target.files)}
            className="text-sm file:mr-2 file:rounded-md file:border file:border-input file:bg-background file:px-2 file:py-1 file:text-sm"
          />
        </div>

        {arquivos.length > 0 ? (
          <ul className="flex flex-col gap-1 px-4 text-sm">
            {arquivos.map((arquivo) => (
              <li
                key={arquivo.name}
                className="flex items-center justify-between gap-2"
              >
                <span className="truncate font-mono text-xs">
                  {arquivo.name}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="xs"
                  onClick={() => remover(arquivo.name)}
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

        <SheetFooter className="flex-row justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={usarBasePreparada}
            disabled={enviando}
          >
            Usar base preparada
          </Button>
          <Button type="button" onClick={enviarUpload} disabled={enviando}>
            {enviando ? "Enviando…" : "Enviar"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
