"use client";

import { useRef, useState } from "react";

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
 * Painel de renomear a coleção (SPEC-0030, FR-010): só o nome exibido muda; o nome
 * físico no Qdrant é fixo. Nome duplicado no Workspace volta como erro do campo e o
 * valor digitado é preservado.
 */

interface RenomearColecaoSheetProps {
  open: boolean;
  colecao: { id: string; nome: string };
  onOpenChange?: (open: boolean) => void;
  onSaved: (colecao: { id: string; nome: string }) => void;
}

export default function RenomearColecaoSheet({ open, colecao, onOpenChange, onSaved }: RenomearColecaoSheetProps) {
  const [nome, setNome] = useState(colecao.nome);
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);
  const campo = useRef<HTMLInputElement>(null);

  function aoMudarAbertura(aberto: boolean) {
    if (salvando) return;
    if (!aberto) {
      setNome(colecao.nome);
      setErro(null);
    }
    onOpenChange?.(aberto);
  }

  async function salvar() {
    if (salvando) return;
    const normalizado = nome.trim();
    if (!normalizado || normalizado.length > 80) {
      setErro("O nome da coleção deve ter de 1 a 80 caracteres.");
      campo.current?.focus();
      return;
    }
    setSalvando(true);
    setErro(null);
    try {
      const salva = await apiJson<{ id: string; nome: string }>(
        `/api/v1/colecoes/${encodeURIComponent(colecao.id)}`,
        {
          method: "PATCH",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ nome: normalizado }),
        },
      );
      onSaved(salva);
    } catch (causa) {
      setErro(
        causa instanceof ApiError && causa.status === 409 && causa.detail
          ? causa.detail
          : "Não foi possível renomear a coleção. Tente novamente.",
      );
      campo.current?.focus();
    } finally {
      setSalvando(false);
    }
  }

  return (
    <Sheet open={open} onOpenChange={aoMudarAbertura}>
      <SheetContent side="right" className="sm:max-w-md">
        <SheetHeader>
          <SheetTitle>Renomear coleção</SheetTitle>
          <SheetDescription>
            Muda só o nome exibido no Workspace; os documentos e a busca continuam os mesmos.
          </SheetDescription>
        </SheetHeader>

        <form
          className="flex min-h-0 flex-1 flex-col gap-4"
          onSubmit={(evento) => {
            evento.preventDefault();
            void salvar();
          }}
        >
          <div className="flex flex-col gap-1.5 px-4">
            <Label htmlFor="colecao-nome">Nome</Label>
            <Input
              ref={campo}
              id="colecao-nome"
              value={nome}
              maxLength={80}
              onChange={(evento) => {
                setNome(evento.target.value);
                if (erro) setErro(null);
              }}
              aria-invalid={erro ? true : undefined}
              aria-describedby={erro ? "colecao-nome-erro" : undefined}
              disabled={salvando}
            />
            {erro ? (
              <Alert id="colecao-nome-erro" variant="destructive" className="mt-1">
                <AlertDescription>{erro}</AlertDescription>
              </Alert>
            ) : null}
          </div>

          <SheetFooter className="flex-row justify-end">
            <Button type="button" variant="outline" onClick={() => aoMudarAbertura(false)} disabled={salvando}>
              Cancelar
            </Button>
            <Button type="submit" loading={salvando} disabled={salvando}>
              {salvando ? "Salvando…" : "Salvar"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
