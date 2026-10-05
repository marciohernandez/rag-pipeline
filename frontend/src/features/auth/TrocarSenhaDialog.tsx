"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api-client";

interface Props {
  open: boolean;
  onOpenChange?: (aberto: boolean) => void;
  onChanged?: () => void;
}

export default function TrocarSenhaDialog({ open, onOpenChange, onChanged }: Props) {
  const campoAtual = useRef<HTMLInputElement>(null);
  const campoNova = useRef<HTMLInputElement>(null);
  const campoConfirmacao = useRef<HTMLInputElement>(null);
  const [atual, setAtual] = useState("");
  const [nova, setNova] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [mostrarSenhas, setMostrarSenhas] = useState(false);
  const [campoErro, setCampoErro] = useState<"atual" | "nova" | "confirmacao" | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (enviando || !erro) return;
    if (campoErro === "atual") campoAtual.current?.focus();
    if (campoErro === "nova") campoNova.current?.focus();
    if (campoErro === "confirmacao") campoConfirmacao.current?.focus();
  }, [campoErro, enviando, erro]);

  function limparFormulario() {
    setAtual("");
    setNova("");
    setConfirmacao("");
    setMostrarSenhas(false);
    setCampoErro(null);
    setErro(null);
  }

  function alterarAberto(aberto: boolean) {
    if (enviando && !aberto) return;
    if (!aberto) limparFormulario();
    onOpenChange?.(aberto);
  }

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
      await apiFetch("/api/v1/auth/senha", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ senha_atual: atual, nova_senha: nova }) });
      onChanged?.();
      limparFormulario();
      onOpenChange?.(false);
    } catch (falha) {
      const mensagem = falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível trocar a senha.";
      const senhaAtualIncorreta = /senha atual/i.test(mensagem);
      setCampoErro(senhaAtualIncorreta ? "atual" : "nova");
      setErro(mensagem);
    } finally {
      setEnviando(false);
    }
  }

  const erroCampo = (campo: typeof campoErro) => campoErro === campo ? erro : null;
  return (
    <Dialog open={open} onOpenChange={alterarAberto}>
      <DialogContent showCloseButton={!enviando}>
        <DialogHeader><DialogTitle>Trocar senha</DialogTitle><DialogDescription>A sessão atual continuará aberta; as outras serão encerradas.</DialogDescription></DialogHeader>
        <form onSubmit={enviar} className="flex flex-col gap-4" noValidate>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="senha-atual">Senha atual</Label>
            <Input
              ref={campoAtual}
              id="senha-atual"
              type={mostrarSenhas ? "text" : "password"}
              autoComplete="current-password"
              value={atual}
              onChange={(evento) => setAtual(evento.target.value)}
              aria-invalid={campoErro === "atual" ? "true" : undefined}
              aria-describedby={campoErro === "atual" ? "erro-senha-atual" : undefined}
              disabled={enviando}
            />
            {erroCampo("atual") ? (
              <p id="erro-senha-atual" role="alert" className="text-sm text-destructive">
                {erroCampo("atual")}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="troca-nova">Nova senha</Label>
            <Input
              ref={campoNova}
              id="troca-nova"
              type={mostrarSenhas ? "text" : "password"}
              autoComplete="new-password"
              value={nova}
              onChange={(evento) => setNova(evento.target.value)}
              aria-invalid={campoErro === "nova" ? "true" : undefined}
              aria-describedby={
                campoErro === "nova"
                  ? "regra-troca-senha erro-troca-nova"
                  : "regra-troca-senha"
              }
              disabled={enviando}
            />
            <p id="regra-troca-senha" className="text-xs text-muted-foreground">
              Mínimo: 10 caracteres.
            </p>
            {erroCampo("nova") ? (
              <p id="erro-troca-nova" role="alert" className="text-sm text-destructive">
                {erroCampo("nova")}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="troca-confirmacao">Confirmar nova senha</Label>
            <Input
              ref={campoConfirmacao}
              id="troca-confirmacao"
              type={mostrarSenhas ? "text" : "password"}
              autoComplete="new-password"
              value={confirmacao}
              onChange={(evento) => setConfirmacao(evento.target.value)}
              aria-invalid={campoErro === "confirmacao" ? "true" : undefined}
              aria-describedby={
                campoErro === "confirmacao" ? "erro-troca-confirmacao" : undefined
              }
              disabled={enviando}
            />
            {erroCampo("confirmacao") ? (
              <p id="erro-troca-confirmacao" role="alert" className="text-sm text-destructive">
                {erroCampo("confirmacao")}
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
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => alterarAberto(false)} disabled={enviando}>
              Cancelar
            </Button>
            <Button type="submit" loading={enviando} disabled={enviando}>
              {enviando ? "Trocando…" : "Trocar senha"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
