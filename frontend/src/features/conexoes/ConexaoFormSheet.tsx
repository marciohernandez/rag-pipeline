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
import { rotulosTipo, type ConexaoResumo } from "@/features/conexoes/DataGridConexoes";
import { ApiError, apiJson } from "@/lib/api-client";

type Campo = "nome" | "modelo" | "urlBase" | "dimensoes" | "url" | "segredo";

interface Props {
  open: boolean;
  conexao?: ConexaoResumo;
  onOpenChange?: (aberto: boolean) => void;
  onSaved?: (conexao: ConexaoResumo) => void;
}

const MODELO_PADRAO = "text-embedding-3-small";
const seletor =
  "h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:bg-input/50 disabled:opacity-50";

function campoDoErro(mensagem: string): Campo {
  if (/url/i.test(mensagem)) return "url";
  if (/chave/i.test(mensagem)) return "segredo";
  if (/dimens/i.test(mensagem)) return "dimensoes";
  if (/modelo/i.test(mensagem)) return "modelo";
  return "nome";
}

/**
 * Criação e edição de conexão em painel lateral (SPEC-0026, FR-002 e FR-014).
 *
 * A chave é somente escrita: na edição o campo nasce vazio e só é enviado
 * quando a pessoa digita uma nova; o painel nunca recebe a chave atual.
 */
export default function ConexaoFormSheet({ open, conexao, onOpenChange, onSaved }: Props) {
  const editando = conexao !== undefined;
  const [tipo, setTipo] = useState(conexao?.tipo ?? "embeddings_openai");
  const [nome, setNome] = useState(conexao?.nome ?? "");
  const [modelo, setModelo] = useState(conexao?.configuracao?.modelo ?? MODELO_PADRAO);
  const [urlBase, setUrlBase] = useState(conexao?.configuracao?.url_base ?? "");
  const [dimensoes, setDimensoes] = useState(String(conexao?.configuracao?.dimensoes ?? 1536));
  const [url, setUrl] = useState(conexao?.configuracao?.url ?? "");
  const [segredo, setSegredo] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [campoErro, setCampoErro] = useState<Campo | null>(null);
  const [salvando, setSalvando] = useState(false);
  const refNome = useRef<HTMLInputElement>(null);
  const refModelo = useRef<HTMLInputElement>(null);
  const refUrlBase = useRef<HTMLInputElement>(null);
  const refDimensoes = useRef<HTMLInputElement>(null);
  const refUrl = useRef<HTMLInputElement>(null);
  const refSegredo = useRef<HTMLInputElement>(null);
  const embeddings = tipo === "embeddings_openai";
  const alterado = editando
    ? nome !== conexao.nome || segredo !== ""
    : nome !== "" || segredo !== "" || url !== "";

  useEffect(() => {
    if (salvando || !erro || !campoErro) return;
    const alvos = {
      nome: refNome,
      modelo: refModelo,
      urlBase: refUrlBase,
      dimensoes: refDimensoes,
      url: refUrl,
      segredo: refSegredo,
    };
    alvos[campoErro].current?.focus();
  }, [campoErro, erro, salvando]);

  function falhar(campo: Campo, mensagem: string) {
    setCampoErro(campo);
    setErro(mensagem);
  }

  function alterarAberto(aberto: boolean) {
    if (aberto) {
      onOpenChange?.(true);
      return;
    }
    if (salvando) return;
    if (alterado && !window.confirm("Descartar alterações não salvas?")) return;
    onOpenChange?.(false);
  }

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setErro(null);
    setCampoErro(null);
    if (!nome.trim()) return falhar("nome", "Informe o nome da conexão.");
    if (embeddings && !modelo.trim()) return falhar("modelo", "Informe o modelo de embeddings.");
    const quantidade = Number(dimensoes);
    if (embeddings && (!Number.isInteger(quantidade) || quantidade < 1)) {
      return falhar("dimensoes", "As dimensões devem ser um inteiro maior que zero.");
    }
    if (!embeddings && !/^https?:\/\//i.test(url.trim())) {
      return falhar("url", "Informe a URL com http:// ou https://.");
    }
    if (embeddings && !editando && !segredo.trim()) {
      return falhar("segredo", "Informe a chave da conexão.");
    }
    const configuracao = embeddings
      ? { modelo: modelo.trim(), dimensoes: quantidade, ...(urlBase.trim() ? { url_base: urlBase.trim() } : {}) }
      : { url: url.trim() };
    setSalvando(true);
    try {
      const salva = await apiJson<ConexaoResumo>(
        editando ? `/api/v1/conexoes/${conexao.id}` : "/api/v1/conexoes",
        {
          method: editando ? "PATCH" : "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            nome: nome.trim(),
            ...(editando ? {} : { tipo }),
            configuracao,
            ...(segredo.trim() ? { segredo: segredo.trim() } : {}),
          }),
        },
      );
      setSegredo("");
      onSaved?.(salva);
      onOpenChange?.(false);
    } catch (falha) {
      const mensagem =
        falha instanceof ApiError && falha.detail ? falha.detail : "Não foi possível salvar a conexão.";
      falhar(campoDoErro(mensagem), mensagem);
    } finally {
      setSalvando(false);
    }
  }

  const erroDe = (campo: Campo) => (campoErro === campo ? erro : null);
  const ligacao = (campo: Campo) => ({
    "aria-invalid": campoErro === campo ? ("true" as const) : undefined,
    "aria-describedby": campoErro === campo ? `erro-conexao-${campo}` : undefined,
    disabled: salvando,
  });
  const mensagemDe = (campo: Campo) =>
    erroDe(campo) ? (
      <p id={`erro-conexao-${campo}`} role="alert" className="text-sm text-destructive">
        {erroDe(campo)}
      </p>
    ) : null;

  return (
    <Sheet open={open} onOpenChange={alterarAberto}>
      <SheetContent side="right" className="w-full" style={{ width: "100%", maxWidth: "32rem" }} showCloseButton={!salvando}>
        <SheetHeader>
          <SheetTitle>{editando ? "Editar conexão" : "Nova conexão"}</SheetTitle>
          <SheetDescription>
            {editando
              ? "Corrija os dados. A chave atual não é exibida: informe uma nova só se quiser trocá-la."
              : "Cadastre uma conexão para reutilizar em qualquer Workspace da equipe."}
          </SheetDescription>
        </SheetHeader>
        <form onSubmit={salvar} className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4" noValidate>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="conexao-nome">Nome</Label>
            <Input ref={refNome} id="conexao-nome" value={nome} onChange={(e) => setNome(e.target.value)} {...ligacao("nome")} />
            {mensagemDe("nome")}
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="conexao-tipo">Tipo</Label>
            <select id="conexao-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)} className={seletor} disabled={salvando || editando}>
              {Object.entries(rotulosTipo).map(([valor, rotulo]) => (
                <option key={valor} value={valor}>
                  {rotulo}
                </option>
              ))}
            </select>
          </div>
          {embeddings ? (
            <>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="conexao-modelo">Modelo</Label>
                <Input ref={refModelo} id="conexao-modelo" value={modelo} onChange={(e) => setModelo(e.target.value)} {...ligacao("modelo")} />
                {mensagemDe("modelo")}
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="conexao-dimensoes">Dimensões</Label>
                <Input ref={refDimensoes} id="conexao-dimensoes" type="number" min={1} value={dimensoes} onChange={(e) => setDimensoes(e.target.value)} {...ligacao("dimensoes")} />
                <p className="text-xs text-muted-foreground">Tamanho do vetor do modelo; precisa coincidir com a coleção.</p>
                {mensagemDe("dimensoes")}
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="conexao-url-base">URL base (opcional)</Label>
                <Input ref={refUrlBase} id="conexao-url-base" value={urlBase} onChange={(e) => setUrlBase(e.target.value)} placeholder="https://api.exemplo.com/v1" {...ligacao("urlBase")} />
                <p className="text-xs text-muted-foreground">Para endpoints compatíveis com a API da OpenAI.</p>
                {mensagemDe("urlBase")}
              </div>
            </>
          ) : (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="conexao-url">URL do Qdrant</Label>
              <Input ref={refUrl} id="conexao-url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://qdrant.exemplo.com" {...ligacao("url")} />
              {mensagemDe("url")}
            </div>
          )}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="conexao-segredo">{embeddings ? "Chave" : "Chave (opcional)"}</Label>
            <Input
              ref={refSegredo}
              id="conexao-segredo"
              type="password"
              autoComplete="new-password"
              value={segredo}
              onChange={(e) => setSegredo(e.target.value)}
              placeholder={editando && conexao.segredo_definido ? conexao.segredo_mascara : undefined}
              {...ligacao("segredo")}
            />
            <p className="text-xs text-muted-foreground">
              {editando ? "Deixe em branco para manter a chave atual." : "A chave é guardada cifrada e nunca é exibida de novo."}
            </p>
            {mensagemDe("segredo")}
          </div>
          <SheetFooter className="-mx-4 flex-row justify-end border-t">
            <Button type="button" variant="outline" onClick={() => alterarAberto(false)} disabled={salvando}>
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
