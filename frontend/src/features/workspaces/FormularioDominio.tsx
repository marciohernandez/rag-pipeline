"use client";

import { useId, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export const TAMANHO_MAXIMO_DOMINIO = 4000;

interface FormularioDominioProps {
  valorInicial: string;
  onSalvar: (texto: string) => Promise<void>;
  rotuloSalvar?: string;
  mensagemSucesso?: string;
  idCampo?: string;
}

/**
 * Campo do resumo do domínio da empresa, compartilhado pela seção do Workspace e pelo
 * passo de confirmação do lote (SPEC-0037, FR-003): contador, erro junto do campo e
 * resultado anunciado em `role="status"`.
 */
export default function FormularioDominio({
  valorInicial,
  onSalvar,
  rotuloSalvar = "Salvar",
  mensagemSucesso = "Resumo salvo.",
  idCampo,
}: FormularioDominioProps) {
  const idPadrao = useId();
  const id = idCampo ?? idPadrao;
  const [texto, setTexto] = useState(valorInicial);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [salvo, setSalvo] = useState(false);

  async function salvar() {
    const limpo = texto.trim();
    setSalvo(false);
    if (!limpo) return setErro("Informe o resumo do domínio.");
    if (limpo.length > TAMANHO_MAXIMO_DOMINIO) {
      return setErro(`O resumo aceita até ${TAMANHO_MAXIMO_DOMINIO} caracteres.`);
    }
    setErro(null);
    setSalvando(true);
    try {
      await onSalvar(limpo);
      setSalvo(true);
    } catch {
      setErro("Não foi possível salvar o resumo; tente novamente.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="flex min-w-0 flex-col gap-2">
      <Label htmlFor={id}>Resumo do domínio</Label>
      <Textarea
        id={id}
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        maxLength={TAMANHO_MAXIMO_DOMINIO + 200}
        disabled={salvando}
        aria-invalid={erro ? true : undefined}
        aria-describedby={`${id}-contador`}
        className="w-full [overflow-wrap:anywhere]"
      />
      <p id={`${id}-contador`} className="text-xs text-muted-foreground">
        {texto.length} de {TAMANHO_MAXIMO_DOMINIO} caracteres
      </p>
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}
      {salvo ? (
        <p role="status" className="text-sm text-muted-foreground">
          {mensagemSucesso}
        </p>
      ) : null}
      <div className="flex flex-col gap-2 sm:flex-row">
        <Button type="button" onClick={salvar} disabled={salvando}>
          {salvando ? "Salvando…" : rotuloSalvar}
        </Button>
      </div>
    </div>
  );
}
