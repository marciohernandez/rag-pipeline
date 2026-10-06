"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

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

interface Props {
  open: boolean;
  pessoa: { id: string; nome: string };
  onOpenChange?: (aberto: boolean) => void;
  onDone?: () => void;
}

export default function RedefinirSenhaDialog({
  open,
  pessoa,
  onOpenChange,
  onDone,
}: Props) {
  const campo = useRef<HTMLInputElement>(null);
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erroLocal, setErroLocal] = useState<string | null>(null);
  const [erroApi, setErroApi] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!enviando && (erroLocal || erroApi)) campo.current?.focus();
  }, [enviando, erroLocal, erroApi]);

  function limparFormulario() {
    setSenha("");
    setMostrarSenha(false);
    setErroLocal(null);
    setErroApi(null);
  }

  function alterarAberto(aberto: boolean) {
    if (enviando && !aberto) return;
    if (!aberto) limparFormulario();
    onOpenChange?.(aberto);
  }

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErroLocal(null);
    setErroApi(null);
    if (senha.length < 10) {
      setErroLocal("A senha precisa ter pelo menos 10 caracteres.");
      return;
    }

    setEnviando(true);
    try {
      await apiFetch(`/api/v1/pessoas/${pessoa.id}/redefinir-senha`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ senha_temporaria: senha }),
      });
      limparFormulario();
      onDone?.();
      onOpenChange?.(false);
    } catch (falha) {
      setErroApi(
        falha instanceof ApiError && falha.detail
          ? falha.detail
          : "Não foi possível redefinir a senha.",
      );
    } finally {
      setEnviando(false);
    }
  }

  const idsDescricao = [
    "regra-senha-temporaria",
    erroLocal ? "erro-senha-temporaria" : null,
    erroApi ? "alerta-redefinir-senha" : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Dialog open={open} onOpenChange={alterarAberto}>
      <DialogContent showCloseButton={!enviando}>
        <DialogHeader>
          <DialogTitle>Redefinir senha</DialogTitle>
          <DialogDescription>
            Defina uma senha temporária para <strong>{pessoa.nome}</strong>. Todas as
            sessões abertas serão encerradas. Na próxima entrada, a pessoa usará esta
            senha e será obrigada a fazer uma nova troca de senha.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={enviar} className="flex flex-col gap-4" noValidate>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="senha-temporaria">Senha temporária</Label>
            <Input
              ref={campo}
              id="senha-temporaria"
              type={mostrarSenha ? "text" : "password"}
              autoComplete="new-password"
              value={senha}
              onChange={(evento) => setSenha(evento.target.value)}
              aria-invalid={erroLocal || erroApi ? "true" : undefined}
              aria-describedby={idsDescricao}
              disabled={enviando}
            />
            <p id="regra-senha-temporaria" className="text-xs text-muted-foreground">
              Mínimo: 10 caracteres.
            </p>
            {erroLocal ? (
              <p id="erro-senha-temporaria" role="alert" className="text-sm text-destructive">
                {erroLocal}
              </p>
            ) : null}
          </div>
          <label className="flex w-fit items-center gap-2 text-sm text-muted-foreground">
            <input
              type="checkbox"
              className="size-4 accent-primary"
              checked={mostrarSenha}
              onChange={(evento) => setMostrarSenha(evento.target.checked)}
              disabled={enviando}
            />
            Mostrar senha
          </label>
          {erroApi ? (
            <Alert id="alerta-redefinir-senha" variant="destructive">
              <AlertDescription>{erroApi}</AlertDescription>
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
            <Button type="submit" loading={enviando} disabled={enviando}>
              {enviando ? (
                <>
                  Redefinindo…
                </>
              ) : (
                "Redefinir senha"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
