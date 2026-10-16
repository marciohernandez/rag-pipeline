"use client";

import { useRef, useState } from "react";

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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, apiJson } from "@/lib/api-client";

const LIMITE = 20000;
const MENSAGEM_FALHA = "Não foi possível interpretar a resposta. Tente novamente.";

interface CaixaRespostaEmpresaProps {
  colecaoId: string;
  provedor: string | null;
  iaPermitida: boolean;
  onInterpretada?: () => void;
}

/**
 * Caixa "Resposta da empresa" (SPEC-0039, FR-001 / NFR-001): o texto só vai à IA depois do
 * aviso confirmado. Com a análise por IA externa desligada, a pessoa decide à mão.
 */
export default function CaixaRespostaEmpresa({
  colecaoId,
  provedor,
  iaPermitida,
  onInterpretada,
}: CaixaRespostaEmpresaProps) {
  const [texto, setTexto] = useState("");
  const [aberto, setAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [erroCampo, setErroCampo] = useState<string | null>(null);
  const campo = useRef<HTMLTextAreaElement>(null);
  const url = `/api/v1/colecoes/${encodeURIComponent(colecaoId)}/decisoes/respostas`;

  function validar(): string | null {
    const limpo = texto.trim();
    if (!limpo) return "Cole a resposta da empresa para continuar.";
    if (limpo.length > LIMITE) return `A resposta da empresa passa de ${LIMITE} caracteres.`;
    return null;
  }

  function pedir() {
    const problema = validar();
    setErroCampo(problema);
    if (problema) {
      campo.current?.focus();
      return;
    }
    if (iaPermitida) setAberto(true);
  }

  async function enviar(corpo: Record<string, unknown>, fechar: boolean) {
    if (enviando) return;
    setEnviando(true);
    setErro(null);
    try {
      await apiJson(url, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(corpo),
      });
      if (fechar) setAberto(false);
      onInterpretada?.();
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setEnviando(false);
    }
  }

  function decidirAMao() {
    const problema = validar();
    setErroCampo(problema);
    if (problema) {
      campo.current?.focus();
      return;
    }
    void enviar({ texto: texto.trim(), manual: true }, false);
  }

  return (
    <section className="flex min-w-0 flex-col gap-3 rounded-lg border bg-card p-4">
      <div className="flex flex-col gap-2">
        <Label htmlFor="resposta-empresa">Resposta da empresa</Label>
        <Textarea
          id="resposta-empresa"
          ref={campo}
          value={texto}
          onChange={(evento) => setTexto(evento.target.value)}
          rows={5}
          aria-invalid={erroCampo ? true : undefined}
          aria-describedby="resposta-empresa-ajuda"
          className="min-w-0"
        />
        <p id="resposta-empresa-ajuda" className="text-xs text-muted-foreground">
          {texto.length} de {LIMITE} caracteres. Cole o texto que a empresa respondeu; anexos não
          são aceitos.
        </p>
        {erroCampo ? (
          <Alert variant="destructive">
            <AlertDescription>{erroCampo}</AlertDescription>
          </Alert>
        ) : null}
      </div>
      {!iaPermitida ? (
        <Alert>
          <AlertDescription>
            A análise por IA externa está desligada neste Workspace. Ative-a para interpretar a
            resposta, ou decida cada contradição à mão.
          </AlertDescription>
        </Alert>
      ) : null}
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
      <div className="flex flex-col gap-2 sm:flex-row sm:justify-end">
        {!iaPermitida ? (
          <Button type="button" variant="outline" onClick={decidirAMao} disabled={enviando}>
            Decidir à mão
          </Button>
        ) : null}
        <Button type="button" onClick={pedir} disabled={enviando}>
          Interpretar resposta
        </Button>
      </div>
      <Dialog open={aberto} onOpenChange={(valor) => !enviando && setAberto(valor)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Interpretar a resposta da empresa?</DialogTitle>
            <DialogDescription>
              O texto da resposta será enviado à IA configurada
              {provedor ? ` (${provedor})` : " no Workspace"} para propor, contradição por
              contradição, qual versão vale. Nenhum documento é alterado sem a sua confirmação.
            </DialogDescription>
          </DialogHeader>
          {erro ? (
            <Alert variant="destructive">
              <AlertDescription>{erro}</AlertDescription>
            </Alert>
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setAberto(false)}
              disabled={enviando}
            >
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={() => enviar({ texto: texto.trim(), confirmado: true }, true)}
              disabled={enviando}
              aria-busy={enviando}
            >
              {enviando ? "Interpretando…" : "Confirmar e interpretar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
