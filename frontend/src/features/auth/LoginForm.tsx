"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiJson } from "@/lib/api-client";
import {
  clearSession,
  consumirAviso,
  saveSession,
  type PessoaSessao,
} from "@/lib/session";

interface RespostaLogin {
  token: string;
  expira_em: string;
  pessoa: PessoaSessao;
}

export default function LoginForm() {
  const router = useRouter();
  const campoEmail = useRef<HTMLInputElement>(null);
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(() => consumirAviso());
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (erro) campoEmail.current?.focus();
  }, [erro]);

  async function aoEnviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    try {
      const resposta = await apiJson<RespostaLogin>("/api/v1/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: email.trim(), senha }),
      });
      saveSession(resposta.token, resposta.pessoa);
      router.push(resposta.pessoa.precisa_trocar_senha ? "/nova-senha" : "/workspaces");
    } catch (falha) {
      clearSession();
      setSenha("");
      setErro(
        falha instanceof ApiError && falha.status === 429
          ? "Conta bloqueada temporariamente. Tente novamente mais tarde."
          : "Não foi possível entrar. Confira o e-mail e a senha e tente novamente.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={aoEnviar} noValidate className="flex w-full flex-col gap-4">
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="login-email">E-mail</Label>
        <Input
          ref={campoEmail}
          id="login-email"
          name="email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(evento) => setEmail(evento.target.value)}
          disabled={enviando}
        />
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="login-senha">Senha</Label>
        <Input
          id="login-senha"
          name="senha"
          type="password"
          autoComplete="current-password"
          value={senha}
          onChange={(evento) => setSenha(evento.target.value)}
          disabled={enviando}
        />
      </div>
      <p className="text-sm text-muted-foreground">
        Esqueceu a senha? Peça a um owner ou admin da sua equipe para redefini-la.
      </p>
      <Button type="submit" disabled={enviando || !email.trim() || !senha}>
        {enviando ? "Entrando…" : "Entrar"}
      </Button>
    </form>
  );
}
