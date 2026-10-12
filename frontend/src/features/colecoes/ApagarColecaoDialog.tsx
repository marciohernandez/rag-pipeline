"use client";

import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";

/**
 * Confirmação de exclusão de coleção (SPEC-0030, FR-011): mostra nome, documentos e
 * chunks e só habilita Apagar quando o nome exato é digitado. A coleção física no
 * Qdrant sai junto; em falha o diálogo continua aberto com uma mensagem segura.
 */

const MENSAGEM_FALHA = "Não foi possível apagar a coleção. Tente novamente.";

interface ApagarColecaoDialogProps {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  colecao: { id: string; nome: string; documentos: number; chunks: number };
  onDeleted: (id: string) => void;
}

export default function ApagarColecaoDialog({
  open,
  onOpenChange,
  colecao,
  onDeleted,
}: ApagarColecaoDialogProps) {
  const [confirmacao, setConfirmacao] = useState("");
  const [apagando, setApagando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const confere = confirmacao === colecao.nome;

  function aoMudarAbertura(aberto: boolean) {
    if (apagando) return;
    if (!aberto) {
      setConfirmacao("");
      setErro(null);
    }
    onOpenChange?.(aberto);
  }

  async function apagar() {
    if (!confere || apagando) return;
    setApagando(true);
    setErro(null);
    try {
      await apiFetch(`/api/v1/colecoes/${encodeURIComponent(colecao.id)}`, {
        method: "DELETE",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ confirmacao_nome: confirmacao }),
      });
      onDeleted(colecao.id);
      onOpenChange?.(false);
    } catch (causa) {
      setErro(
        causa instanceof ApiError && causa.status === 409 && causa.detail ? causa.detail : MENSAGEM_FALHA,
      );
    } finally {
      setApagando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={aoMudarAbertura}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Apagar a coleção “{colecao.nome}”?</DialogTitle>
          <DialogDescription>
            Serão apagados {colecao.documentos} documentos e {colecao.chunks} chunks, o histórico de envios, as
            consultas e a coleção no Qdrant. Não é possível desfazer.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-1.5">
          <Label htmlFor="apagar-colecao-nome">Digite o nome da coleção para confirmar</Label>
          <Input
            id="apagar-colecao-nome"
            value={confirmacao}
            onChange={(evento) => setConfirmacao(evento.target.value)}
            autoComplete="off"
            disabled={apagando}
          />
        </div>

        {erro ? (
          <Alert variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => aoMudarAbertura(false)} disabled={apagando}>
            Cancelar
          </Button>
          <Button type="button" variant="destructive" onClick={apagar} loading={apagando} disabled={!confere || apagando}>
            {apagando ? "Apagando…" : "Apagar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
