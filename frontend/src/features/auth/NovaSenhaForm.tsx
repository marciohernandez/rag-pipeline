"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";

export default function NovaSenhaForm() {
  const router = useRouter();
  const campoNova = useRef<HTMLInputElement>(null);
  const campoConfirmacao = useRef<HTMLInputElement>(null);
  const [nova, setNova] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [mostrarSenhas, setMostrarSenhas] = useState(false);
  const [campoErro, setCampoErro] = useState<"nova" | "confirmacao" | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (enviando || !erro) return;
    if (campoErro === "nova") campoNova.current?.focus();
    if (campoErro === "confirmacao") campoConfirmacao.current?.focus();
  }, [campoErro, enviando, erro]);

  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setCampoErro(null);
    if (nova.length < 10) {
      setCampoErro("nova");
      setErro("A senha precisa ter pelo menos 10 caracteres.");
      return;
    }
    if (nova !== confirmacao) {
      setCampoErro("confirmacao");
      setErro("As senhas não conferem.");
      return;
    }
    setEnviando(true);
    try {
      await apiFetch("/api/v1/auth/senha", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ nova_senha: nova }),
      });
      router.push("/workspaces");
    } catch (falha) {
      setCampoErro("nova");
      setErro(
        falha instanceof ApiError && falha.detail
          ? falha.detail
          : "Não foi possível definir a senha. Tente novamente.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={enviar} noValidate>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="nova-senha">Nova senha</Label>
        <Input
          ref={campoNova}
          id="nova-senha"
          type={mostrarSenhas ? "text" : "password"}
          autoComplete="new-password"
          value={nova}
          onChange={(evento) => setNova(evento.target.value)}
          aria-invalid={campoErro === "nova" ? "true" : undefined}
          aria-describedby={
            campoErro === "nova"
              ? "regra-nova-senha erro-nova-senha"
              : "regra-nova-senha"
          }
          disabled={enviando}
        />
        <p id="regra-nova-senha" className="text-xs text-muted-foreground">
          Mínimo: 10 caracteres.
        </p>
        {campoErro === "nova" && erro ? (
          <p id="erro-nova-senha" role="alert" className="text-sm text-destructive">
            {erro}
          </p>
        ) : null}
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="confirmar-nova-senha">Confirmar nova senha</Label>
        <Input
          ref={campoConfirmacao}
          id="confirmar-nova-senha"
          type={mostrarSenhas ? "text" : "password"}
          autoComplete="new-password"
          value={confirmacao}
          onChange={(evento) => setConfirmacao(evento.target.value)}
          aria-invalid={campoErro === "confirmacao" ? "true" : undefined}
          aria-describedby={
            campoErro === "confirmacao" ? "erro-confirmar-nova-senha" : undefined
          }
          disabled={enviando}
        />
        {campoErro === "confirmacao" && erro ? (
          <p
            id="erro-confirmar-nova-senha"
            role="alert"
            className="text-sm text-destructive"
          >
            {erro}
          </p>
        ) : null}
      </div>
      <label className="flex w-fit items-center gap-2 text-sm text-muted-foreground">
        <input
          type="checkbox"
          className="size-4 accent-primary"
          checked={mostrarSenhas}
          onChange={(evento) => setMostrarSenhas(evento.target.checked)}
          disabled={enviando}
        />
        Mostrar senhas
      </label>
      {erro && campoErro === null ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
      <Button type="submit" loading={enviando} disabled={enviando}>
        {enviando ? "Definindo…" : "Definir senha"}
      </Button>
    </form>
  );
}
