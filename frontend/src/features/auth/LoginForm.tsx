"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api-client";
import { clearSession, saveSession } from "@/lib/session";

/**
 * Formulário de Login por token de demonstração (SPEC-0013, US-001).
 *
 * Um campo (token, `type=password`), ação "Entrar" e erro genérico inline.
 * A validação do token é uma leitura autenticada leve (`GET /api/v1/bases`):
 * 200 guarda a sessão e leva aos Workspaces; qualquer falha limpa a sessão e
 * mostra uma mensagem sem detalhe do backend (NFR-002).
 */

const MENSAGEM_ERRO =
  "Não foi possível entrar com esse token. Verifique e tente novamente.";

export default function LoginForm() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    saveSession(token);
    try {
      await apiFetch("/api/v1/bases");
      router.push("/workspaces");
    } catch {
      clearSession();
      setErro(MENSAGEM_ERRO);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={aoEnviar} noValidate className="flex w-full flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="token">Token de demonstração</Label>
        <Input
          id="token"
          name="token"
          type="password"
          autoComplete="off"
          value={token}
          onChange={(evento) => setToken(evento.target.value)}
          aria-invalid={erro !== null}
          aria-describedby={erro ? "token-erro" : undefined}
        />
        {erro ? (
          <Alert id="token-erro" variant="destructive">
            <AlertDescription>{erro}</AlertDescription>
          </Alert>
        ) : null}
      </div>
      <Button type="submit" disabled={enviando}>
        {enviando ? "Entrando…" : "Entrar"}
      </Button>
    </form>
  );
}
