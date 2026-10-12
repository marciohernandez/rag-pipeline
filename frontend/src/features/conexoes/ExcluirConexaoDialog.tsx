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
import { ApiError, apiFetch } from "@/lib/api-client";

interface Props {
  open: boolean;
  onOpenChange?: (open: boolean) => void;
  conexao: { id: string; nome: string; em_uso: number };
  onDeleted: (id: string) => void;
}

/**
 * Confirma a exclusão definitiva de uma conexão (SPEC-0026, FR-003). Uma
 * conexão em uso não pode ser excluída: o diálogo explica e oferece apenas
 * Cancelar, porque desativar preserva vínculos e histórico.
 */
export default function ExcluirConexaoDialog({ open, onOpenChange, conexao, onDeleted }: Props) {
  const [excluindo, setExcluindo] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const emUso = conexao.em_uso > 0;

  async function excluir() {
    setExcluindo(true);
    setErro(null);
    try {
      await apiFetch(`/api/v1/conexoes/${conexao.id}`, { method: "DELETE" });
      onDeleted(conexao.id);
      onOpenChange?.(false);
    } catch (falha) {
      setErro(
        falha instanceof ApiError && falha.detail
          ? falha.detail
          : "Não foi possível excluir a conexão. Tente novamente.",
      );
    } finally {
      setExcluindo(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Excluir a conexão “{conexao.nome}”?</DialogTitle>
          <DialogDescription>
            {emUso
              ? `Esta conexão está em uso por ${conexao.em_uso} coleção(ões) e não pode ser excluída. Desative-a para impedir novas publicações sem perder o histórico.`
              : "A conexão e a chave guardada serão removidas definitivamente. Não é possível desfazer."}
          </DialogDescription>
        </DialogHeader>
        {erro ? (
          <Alert variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange?.(false)} disabled={excluindo}>
            Cancelar
          </Button>
          {emUso ? null : (
            <Button type="button" variant="destructive" onClick={excluir} loading={excluindo} disabled={excluindo}>
              {excluindo ? "Excluindo…" : "Excluir"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
