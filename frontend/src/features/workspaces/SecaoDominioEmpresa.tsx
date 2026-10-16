"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import ConexaoFormSheet from "@/features/conexoes/ConexaoFormSheet";
import type { ConexaoResumo } from "@/features/conexoes/DataGridConexoes";
import FormularioDominio from "@/features/workspaces/FormularioDominio";
import { apiJson } from "@/lib/api-client";

const PAPEIS_DE_ESCRITA = ["owner", "admin"];

interface VersaoDominio {
  versao: number | null;
  texto: string;
  vigente?: boolean;
  aprovado_por_nome?: string | null;
  criado_em?: string;
}

interface AnaliseIa {
  ia_externa_permitida: boolean;
  conexao_ia_id: string | null;
}

/**
 * Seção "Domínio da empresa" do Workspace (SPEC-0037, US-002/US-003): resumo vigente,
 * histórico (owner/admin), conexão de IA e a chave "permitir análise por IA externa".
 * `member` só consulta o resumo vigente.
 */
export default function SecaoDominioEmpresa({
  workspaceId,
  papel,
}: {
  workspaceId: string;
  papel?: string;
}) {
  const podeEscrever = papel !== undefined && PAPEIS_DE_ESCRITA.includes(papel);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [vigente, setVigente] = useState<VersaoDominio | null>(null);
  const [versoes, setVersoes] = useState<VersaoDominio[]>([]);
  const [analise, setAnalise] = useState<AnaliseIa>({
    ia_externa_permitida: false,
    conexao_ia_id: null,
  });
  const [conexoes, setConexoes] = useState<ConexaoResumo[]>([]);
  const [novaConexao, setNovaConexao] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const [tentativa, setTentativa] = useState(0);
  const base = `/api/v1/workspaces/${workspaceId}`;

  useEffect(() => {
    let cancelado = false;
    (async () => {
      try {
        const atual = await apiJson<VersaoDominio>(`${base}/dominio`);
        if (cancelado) return;
        setVigente(atual && typeof atual === "object" ? atual : { versao: null, texto: "" });
        if (podeEscrever) {
          const [historico, ia, lista] = await Promise.all([
            apiJson<VersaoDominio[]>(`${base}/dominio/versoes`),
            apiJson<AnaliseIa>(`${base}/analise-ia`),
            apiJson<ConexaoResumo[]>("/api/v1/conexoes"),
          ]);
          if (cancelado) return;
          setVersoes(Array.isArray(historico) ? historico : []);
          if (ia && typeof ia === "object" && "ia_externa_permitida" in ia) setAnalise(ia);
          setConexoes(Array.isArray(lista) ? lista : []);
        }
      } catch {
        if (!cancelado) setErro("Não foi possível carregar o domínio da empresa; tente novamente.");
      } finally {
        if (!cancelado) setCarregando(false);
      }
    })();
    return () => {
      cancelado = true;
    };
  }, [base, podeEscrever, tentativa]);

  async function salvarDominio(texto: string) {
    const nova = await apiJson<VersaoDominio>(`${base}/dominio`, {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ texto }),
    });
    setVigente(nova);
    setVersoes((antes) => [nova, ...antes.map((v) => ({ ...v, vigente: false }))]);
  }

  async function alterarAnalise(parcial: Partial<AnaliseIa>) {
    setAviso(null);
    try {
      const atualizada = await apiJson<AnaliseIa>(`${base}/analise-ia`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(parcial),
      });
      setAnalise(atualizada);
      setAviso("Configuração de IA salva.");
    } catch {
      setAviso("Não foi possível salvar a configuração de IA.");
    }
  }

  const conexoesDeIa = conexoes.filter((c) => c.tipo === "ia_analise" && c.situacao === "ativa");

  return (
    <section
      id="dominio-da-empresa"
      aria-labelledby="titulo-dominio-da-empresa"
      aria-busy={carregando}
      className="flex min-w-0 flex-col gap-4 rounded-lg border p-4"
    >
      <h2 id="titulo-dominio-da-empresa" className="text-lg font-medium">
        Domínio da empresa
      </h2>
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-col gap-2">
            {erro}
            <Button type="button" size="sm" variant="outline" onClick={() => {
                setCarregando(true);
                setErro(null);
                setTentativa((t) => t + 1);
              }}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}
      {carregando ? (
        <Skeleton className="h-24 w-full" />
      ) : podeEscrever ? (
        <FormularioDominio
          key={vigente?.versao ?? "vazio"}
          valorInicial={vigente?.texto ?? ""}
          onSalvar={salvarDominio}
          mensagemSucesso="Resumo salvo como nova versão."
        />
      ) : (
        <p className="text-sm [overflow-wrap:anywhere]">
          {vigente?.texto || "Nenhum resumo do domínio foi confirmado ainda."}
        </p>
      )}
      {podeEscrever && !carregando ? (
        <>
          <div className="flex min-w-0 flex-col gap-3 border-t pt-4">
            <div className="flex items-center gap-2">
              <Checkbox
                id="ia-externa"
                checked={analise.ia_externa_permitida}
                onCheckedChange={(marcada) =>
                  void alterarAnalise({ ia_externa_permitida: marcada === true })
                }
              />
              <Label htmlFor="ia-externa">Permitir análise por IA externa</Label>
            </div>
            <div className="flex min-w-0 flex-col gap-1.5">
              <Label htmlFor="conexao-ia">Conexão de IA para análise</Label>
              <select
                id="conexao-ia"
                value={analise.conexao_ia_id ?? ""}
                onChange={(e) => void alterarAnalise({ conexao_ia_id: e.target.value || null })}
                className="h-9 w-full min-w-0 rounded-lg border border-input bg-transparent px-2.5 text-sm"
              >
                <option value="">Nenhuma</option>
                {conexoesDeIa.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="self-start"
                onClick={() => setNovaConexao(true)}
              >
                Cadastrar conexão
              </Button>
            </div>
            {aviso ? (
              <p role="status" className="text-sm text-muted-foreground">
                {aviso}
              </p>
            ) : null}
          </div>
          <details className="border-t pt-4">
            <summary className="cursor-pointer text-sm font-medium">
              Histórico de versões ({versoes.length})
            </summary>
            <ul className="mt-2 flex flex-col gap-2 text-sm">
              {versoes.map((v) => (
                <li key={v.versao} className="min-w-0 [overflow-wrap:anywhere]">
                  <strong>Versão {v.versao}</strong>
                  {v.vigente ? " (vigente)" : ""}
                  {v.aprovado_por_nome ? ` — ${v.aprovado_por_nome}` : ""}: {v.texto}
                </li>
              ))}
            </ul>
          </details>
          <ConexaoFormSheet
            open={novaConexao}
            onOpenChange={setNovaConexao}
            onSaved={(conexao) => {
              setConexoes((antes) => [...antes, conexao]);
              void alterarAnalise({ conexao_ia_id: conexao.id });
            }}
          />
        </>
      ) : null}
    </section>
  );
}
