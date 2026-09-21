"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

interface ParMetadado {
  id: number;
  rotulo: string;
  valor: string;
}

interface UploadBaseSheetProps {
  open: boolean;
  workspaceId?: string;
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
  workspaceId,
  onOpenChange,
  onCreated,
}: UploadBaseSheetProps) {
  const router = useRouter();
  const [arquivos, setArquivos] = useState<File[]>([]);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [colecao, setColecao] = useState("");
  const [pares, setPares] = useState<ParMetadado[]>([]);
  const [rotuloInvalido, setRotuloInvalido] = useState<number | null>(null);
  const [focoPendente, setFocoPendente] = useState<{ destino: number | "adicionar" } | null>(null);
  const proximoId = useRef(0);
  const rotulosRef = useRef(new Map<number, HTMLInputElement>());
  const adicionarRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!focoPendente) return;
    if (focoPendente.destino === "adicionar") adicionarRef.current?.focus();
    else rotulosRef.current.get(focoPendente.destino)?.focus();
  }, [focoPendente]);

  function adicionarPar() {
    const id = ++proximoId.current;
    setPares((atuais) => [...atuais, { id, rotulo: "", valor: "" }]);
    setFocoPendente({ destino: id });
  }

  function atualizarPar(id: number, campo: "rotulo" | "valor", valor: string) {
    setPares((atuais) => atuais.map((par) =>
      par.id === id ? { ...par, [campo]: valor } : par,
    ));
    setErro(null);
    setRotuloInvalido(null);
  }

  function removerPar(id: number) {
    const indice = pares.findIndex((par) => par.id === id);
    const restantes = pares.filter((par) => par.id !== id);
    setPares(restantes);
    setErro(null);
    setRotuloInvalido(null);
    rotulosRef.current.delete(id);
    setFocoPendente({ destino: restantes[indice]?.id ?? restantes[indice - 1]?.id ?? "adicionar" });
  }

  function validarPares(): boolean {
    const vistos = new Set<string>();
    for (const par of pares) {
      const rotulo = par.rotulo.trim();
      if (!rotulo) {
        setErro("Informe o rótulo de cada metadado.");
        setRotuloInvalido(par.id);
        rotulosRef.current.get(par.id)?.focus();
        return false;
      }
      if (vistos.has(rotulo)) {
        setErro(`Rótulo de metadado repetido: ${rotulo}.`);
        setRotuloInvalido(par.id);
        rotulosRef.current.get(par.id)?.focus();
        return false;
      }
      vistos.add(rotulo);
    }
    return true;
  }

  function preencherCampos(body: FormData | URLSearchParams) {
    if (workspaceId) body.set("workspace_id", workspaceId);
    if (colecao.trim()) body.set("collection_name", colecao.trim());
    body.set("metadados_chunk", JSON.stringify(
      pares.map(({ rotulo, valor }) => ({ rotulo: rotulo.trim(), valor })),
    ));
  }

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
      setColecao("");
      setPares([]);
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
    if (!validarPares()) return;
    const corpo = new FormData();
    for (const arquivo of arquivos) {
      corpo.append("arquivos", arquivo, arquivo.name);
    }
    preencherCampos(corpo);
    void criar(corpo, "Não foi possível enviar a base. Tente novamente.");
  }

  function usarBasePreparada() {
    if (!validarPares()) return;
    const corpo = new URLSearchParams({ usar_base_preparada: "true" });
    preencherCampos(corpo);
    void criar(
      corpo,
      "Não foi possível usar a base preparada. Tente novamente.",
    );
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Enviar base</SheetTitle>
          <SheetDescription>
            Envie arquivos Markdown (.md) ou use a base preparada de
            demonstração.
          </SheetDescription>
          {workspaceId ? (
            <p className="pt-2 font-mono text-xs text-muted-foreground break-all">
              Workspace: {workspaceId}
            </p>
          ) : null}
        </SheetHeader>

        <div className="flex flex-col gap-1.5 px-4">
          <Label htmlFor="arquivos">Arquivos Markdown</Label>
          <input
            id="arquivos"
            type="file"
            multiple
            accept=".md"
            onChange={(evento) => aoSelecionar(evento.target.files)}
            disabled={enviando}
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
                  disabled={enviando}
                >
                  Remover
                </Button>
              </li>
            ))}
          </ul>
        ) : null}

        <div className="flex flex-col gap-1.5 px-4">
          <Label htmlFor="collection-name">Nome da coleção</Label>
          <Input
            id="collection-name"
            value={colecao}
            onChange={(evento) => setColecao(evento.target.value)}
            aria-describedby="collection-name-hint"
            disabled={enviando}
          />
          <p id="collection-name-hint" className="text-xs text-muted-foreground">
            Deixe em branco para usar o padrão deste Workspace.
          </p>
        </div>

        <section className="flex flex-col gap-3 px-4" aria-labelledby="metadados-titulo">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 id="metadados-titulo" className="text-sm font-medium">Metadados dos chunks</h3>
              <p className="text-xs text-muted-foreground">
                Pares opcionais aplicados a todos os chunks desta Base.
              </p>
            </div>
            <Button
              ref={adicionarRef}
              type="button"
              variant="outline"
              size="sm"
              onClick={adicionarPar}
              disabled={enviando}
            >
              Adicionar metadado
            </Button>
          </div>
          {pares.map((par, indice) => (
            <div key={par.id} className="rounded-lg border p-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div className="flex min-w-0 flex-col gap-1.5">
                  <Label htmlFor={`metadado-rotulo-${par.id}`}>Rótulo {indice + 1}</Label>
                  <Input
                    ref={(elemento) => {
                      if (elemento) rotulosRef.current.set(par.id, elemento);
                      else rotulosRef.current.delete(par.id);
                    }}
                    id={`metadado-rotulo-${par.id}`}
                    value={par.rotulo}
                    onChange={(evento) => atualizarPar(par.id, "rotulo", evento.target.value)}
                    aria-required="true"
                    aria-invalid={rotuloInvalido === par.id ? true : undefined}
                    aria-describedby={rotuloInvalido === par.id ? "upload-base-erro" : undefined}
                    disabled={enviando}
                  />
                </div>
                <div className="flex min-w-0 flex-col gap-1.5">
                  <Label htmlFor={`metadado-valor-${par.id}`}>Valor {indice + 1}</Label>
                  <Input
                    id={`metadado-valor-${par.id}`}
                    value={par.valor}
                    onChange={(evento) => atualizarPar(par.id, "valor", evento.target.value)}
                    disabled={enviando}
                  />
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="mt-2"
                aria-label={`Remover metadado ${indice + 1}`}
                onClick={() => removerPar(par.id)}
                disabled={enviando}
              >
                Remover
              </Button>
            </div>
          ))}
        </section>

        {erro ? (
          <Alert id="upload-base-erro" variant="destructive" className="mx-4 w-auto">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}

        <SheetFooter className="sm:flex-row sm:justify-end">
          <Button
            type="button"
            variant="outline"
            onClick={usarBasePreparada}
            disabled={enviando}
            className="w-full sm:w-auto"
          >
            Usar base preparada
          </Button>
          <Button type="button" onClick={enviarUpload} disabled={enviando} className="w-full sm:w-auto">
            {enviando ? "Enviando…" : "Enviar"}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
