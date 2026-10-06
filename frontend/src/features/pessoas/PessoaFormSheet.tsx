"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { PessoaResumo } from "@/features/pessoas/DataGridPessoas";
import { ApiError, apiJson } from "@/lib/api-client";

interface Props {
  open: boolean;
  pessoa?: PessoaResumo;
  podeAtribuirOwner?: boolean;
  onOpenChange?: (aberto: boolean) => void;
  onSaved?: (pessoa: PessoaResumo) => void;
}

type CampoErro = "nome" | "email" | "senha" | null;

export default function PessoaFormSheet({
  open,
  pessoa,
  podeAtribuirOwner = false,
  onOpenChange,
  onSaved,
}: Props) {
  const [nome, setNome] = useState(pessoa?.nome ?? "");
  const [email, setEmail] = useState(pessoa?.email ?? "");
  const [papel, setPapel] = useState(pessoa?.papel ?? "member");
  const [senha, setSenha] = useState("");
  const [mostrarSenha, setMostrarSenha] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [campoErro, setCampoErro] = useState<CampoErro>(null);
  const [salvando, setSalvando] = useState(false);
  const campoNome = useRef<HTMLInputElement>(null);
  const campoEmail = useRef<HTMLInputElement>(null);
  const campoSenha = useRef<HTMLInputElement>(null);
  const editando = pessoa !== undefined;
  const alterado =
    nome !== (pessoa?.nome ?? "") ||
    email !== (pessoa?.email ?? "") ||
    papel !== (pessoa?.papel ?? "member") ||
    (!editando && senha !== "");

  useEffect(() => {
    if (salvando || !erro) return;
    if (campoErro === "nome") campoNome.current?.focus();
    if (campoErro === "email") campoEmail.current?.focus();
    if (campoErro === "senha") campoSenha.current?.focus();
  }, [campoErro, erro, salvando]);

  function restaurar() {
    setNome(pessoa?.nome ?? "");
    setEmail(pessoa?.email ?? "");
    setPapel(pessoa?.papel ?? "member");
    setSenha("");
    setMostrarSenha(false);
    setErro(null);
    setCampoErro(null);
  }

  function alterarAberto(aberto: boolean) {
    if (aberto) {
      onOpenChange?.(true);
      return;
    }
    if (salvando) return;
    if (alterado && !window.confirm("Descartar alterações não salvas?")) return;
    restaurar();
    onOpenChange?.(false);
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setCampoErro(null);
    if (!nome.trim()) {
      setCampoErro("nome");
      setErro("Informe o nome.");
      return;
    }
    if (!email.includes("@")) {
      setCampoErro("email");
      setErro("Informe um e-mail válido.");
      return;
    }
    if (!editando && senha.length < 10) {
      setCampoErro("senha");
      setErro("A senha precisa ter pelo menos 10 caracteres.");
      return;
    }
    setSalvando(true);
    try {
      const salvo = await apiJson<PessoaResumo>(
        editando ? `/api/v1/pessoas/${pessoa.id}` : "/api/v1/pessoas",
        {
          method: editando ? "PATCH" : "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify(
            editando
              ? { nome: nome.trim(), email: email.trim(), papel }
              : {
                  nome: nome.trim(),
                  email: email.trim(),
                  papel,
                  senha_inicial: senha,
                },
          ),
        },
      );
      restaurar();
      onSaved?.(salvo);
      onOpenChange?.(false);
    } catch (falha) {
      const mensagem =
        falha instanceof ApiError && falha.detail
          ? falha.detail
          : "Não foi possível salvar a pessoa.";
      const duplicado =
        falha instanceof ApiError && falha.status === 409 && /e-mail/i.test(mensagem);
      setCampoErro(duplicado ? "email" : "nome");
      setErro(mensagem);
    } finally {
      setSalvando(false);
    }
  }

  const erroDe = (campo: CampoErro) => (campoErro === campo ? erro : null);

  return (
    <Sheet open={open} onOpenChange={alterarAberto}>
      <SheetContent
        side="right"
        className="w-full"
        style={{ width: "100%", maxWidth: "32rem" }}
        showCloseButton={!salvando}
      >
        <SheetHeader>
          <SheetTitle>{editando ? "Editar pessoa" : "Nova pessoa"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Corrija os dados e o papel desta pessoa."
              : "Crie o acesso e compartilhe a senha inicial por um canal seguro."}
          </SheetDescription>
        </SheetHeader>
        <form
          onSubmit={salvar}
          className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4"
          noValidate
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pessoa-nome">Nome</Label>
            <Input
              ref={campoNome}
              id="pessoa-nome"
              value={nome}
              onChange={(evento) => setNome(evento.target.value)}
              aria-invalid={campoErro === "nome" ? "true" : undefined}
              aria-describedby={campoErro === "nome" ? "erro-pessoa-nome" : undefined}
              disabled={salvando}
            />
            {erroDe("nome") ? (
              <p id="erro-pessoa-nome" role="alert" className="text-sm text-destructive">
                {erroDe("nome")}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pessoa-email">E-mail</Label>
            <Input
              ref={campoEmail}
              id="pessoa-email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(evento) => setEmail(evento.target.value)}
              aria-invalid={campoErro === "email" ? "true" : undefined}
              aria-describedby={campoErro === "email" ? "erro-pessoa-email" : undefined}
              disabled={salvando}
            />
            {erroDe("email") ? (
              <p id="erro-pessoa-email" role="alert" className="text-sm text-destructive">
                {erroDe("email")}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="pessoa-papel">Papel</Label>
            <select
              id="pessoa-papel"
              value={papel}
              onChange={(evento) => setPapel(evento.target.value)}
              className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50"
              disabled={salvando}
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
              {podeAtribuirOwner ? <option value="owner">Owner</option> : null}
            </select>
          </div>
          {!editando ? (
            <>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="pessoa-senha">Senha inicial</Label>
                <Input
                  ref={campoSenha}
                  id="pessoa-senha"
                  type={mostrarSenha ? "text" : "password"}
                  autoComplete="new-password"
                  value={senha}
                  onChange={(evento) => setSenha(evento.target.value)}
                  aria-invalid={campoErro === "senha" ? "true" : undefined}
                  aria-describedby={
                    campoErro === "senha"
                      ? "regra-pessoa-senha erro-pessoa-senha"
                      : "regra-pessoa-senha"
                  }
                  disabled={salvando}
                />
                <p id="regra-pessoa-senha" className="text-xs text-muted-foreground">
                  Mínimo: 10 caracteres.
                </p>
                {erroDe("senha") ? (
                  <p id="erro-pessoa-senha" role="alert" className="text-sm text-destructive">
                    {erroDe("senha")}
                  </p>
                ) : null}
              </div>
              <label className="flex w-fit items-center gap-2 text-sm text-muted-foreground">
                <input
                  type="checkbox"
                  className="size-4 accent-primary"
                  checked={mostrarSenha}
                  onChange={(evento) => setMostrarSenha(evento.target.checked)}
                  disabled={salvando}
                />
                Mostrar senha
              </label>
            </>
          ) : null}
          <SheetFooter className="-mx-4 flex-row justify-end border-t">
            <Button
              type="button"
              variant="outline"
              onClick={() => alterarAberto(false)}
              disabled={salvando}
            >
              Cancelar
            </Button>
            <Button type="submit" loading={salvando} disabled={salvando}>
              {salvando ? "Salvando…" : "Salvar"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
