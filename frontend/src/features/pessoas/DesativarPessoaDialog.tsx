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
import { Spinner } from "@/components/ui/spinner";
import { apiFetch } from "@/lib/api-client";

interface Props {
  open: boolean;
  pessoa: { id: string; nome: string };
  acao: "desativar" | "reativar";
  bloqueio?: string;
  onOpenChange?: (aberto: boolean) => void;
  onDone?: () => void;
}

export default function DesativarPessoaDialog({
  open,
  pessoa,
  acao,
  bloqueio,
  onOpenChange,
  onDone,
}: Props) {
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const desativando = acao === "desativar";
  const titulo = desativando ? "Desativar pessoa" : "Reativar pessoa";
  const rotuloAcao = desativando ? "Desativar" : "Reativar";

  function alterarAberto(aberto: boolean) {
    if (enviando && !aberto) return;
    if (!aberto) setErro(null);
    onOpenChange?.(aberto);
  }

  async function confirmar() {
    setEnviando(true);
    setErro(null);
    try {
      await apiFetch(`/api/v1/pessoas/${pessoa.id}/${acao}`, { method: "POST" });
      setErro(null);
      onDone?.();
      onOpenChange?.(false);
    } catch {
      setErro(`Não foi possível ${acao} esta pessoa.`);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={alterarAberto}>
      <DialogContent showCloseButton={!enviando}>
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
          <DialogDescription>
            {desativando ? (
              <>
                Desativar <strong>{pessoa.nome}</strong>? A pessoa perderá o acesso
                imediatamente: cada sessão aberta termina agora e uma nova entrada
                ficará bloqueada até a reativação.
              </>
            ) : (
              <>
                Reativar <strong>{pessoa.nome}</strong>? A pessoa poderá entrar novamente
                com as credenciais atuais. Esta ação não cria nem envia uma nova senha.
              </>
            )}
          </DialogDescription>
        </DialogHeader>
        {bloqueio ? (
          <Alert>
            <AlertDescription>{bloqueio}</AlertDescription>
          </Alert>
        ) : null}
        {erro ? (
          <Alert variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}
        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => alterarAberto(false)}
            disabled={enviando}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            variant={desativando ? "destructive" : "default"}
            disabled={enviando || Boolean(bloqueio)}
            onClick={() => void confirmar()}
          >
            {enviando ? (
              <>
                <Spinner aria-hidden /> {desativando ? "Desativando…" : "Reativando…"}
              </>
            ) : (
              rotuloAcao
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
