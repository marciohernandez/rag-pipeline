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
import { ApiError, apiJson } from "@/lib/api-client";

interface BotaoAnalisarContradicoesProps {
  colecaoId: string;
  provedor: string | null;
  onIniciada?: (analiseId: string) => void;
}

const MENSAGEM_FALHA = "Não foi possível iniciar a análise. Tente novamente.";

/**
 * Botão "Analisar contradições" com aviso de envio à IA (SPEC-0038, FR-001 / NFR-001): o
 * conteúdo só é enviado depois da confirmação.
 */
export default function BotaoAnalisarContradicoes({
  colecaoId,
  provedor,
  onIniciada,
}: BotaoAnalisarContradicoesProps) {
  const [aberto, setAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  function aoMudarAbertura(valor: boolean) {
    if (enviando) return;
    if (!valor) setErro(null);
    setAberto(valor);
  }

  async function confirmar() {
    if (enviando) return;
    setEnviando(true);
    setErro(null);
    try {
      const analise = await apiJson<{ id: string }>(
        `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/contradicoes/analises`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ confirmado: true }),
        },
      );
      setAberto(false);
      onIniciada?.(analise.id);
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <>
      <Button type="button" variant="outline" onClick={() => setAberto(true)}>
        Analisar contradições
      </Button>
      <Dialog open={aberto} onOpenChange={aoMudarAbertura}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Analisar contradições da coleção?</DialogTitle>
            <DialogDescription>
              O conteúdo dos documentos será enviado à IA configurada
              {provedor ? ` (${provedor})` : " no Workspace"} para comparar as informações entre
              eles. Nenhum documento é alterado: o resultado é um relatório para você conferir.
            </DialogDescription>
          </DialogHeader>
          {erro ? (
            <Alert variant="destructive">
              <AlertDescription>{erro}</AlertDescription>
            </Alert>
          ) : null}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => aoMudarAbertura(false)} disabled={enviando}>
              Cancelar
            </Button>
            <Button type="button" onClick={confirmar} disabled={enviando} aria-busy={enviando}>
              {enviando ? "Analisando…" : "Confirmar e analisar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
