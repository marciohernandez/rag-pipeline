"use client";

import { useSearchParams } from "next/navigation";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ConsultaColecao from "@/features/colecoes/ConsultaColecao";
import DataGridDocumentos from "@/features/colecoes/DataGridDocumentos";
import DataGridEnvios from "@/features/colecoes/DataGridEnvios";
import type { DocumentoResumo, EnvioResumo } from "@/features/colecoes/tipos";

/**
 * Abas do detalhe da coleção (SPEC-0030, FR-008): Documentos, Envios e Consulta. A aba
 * ativa vive na URL (`?aba=`) e a página abre em Documentos. Setas movem o foco entre as
 * abas; só o painel ativo é montado.
 */

const ABAS = [
  { valor: "documentos", rotulo: "Documentos" },
  { valor: "envios", rotulo: "Envios" },
  { valor: "consulta", rotulo: "Consulta" },
] as const;

type Aba = (typeof ABAS)[number]["valor"];

interface AbasColecaoProps {
  workspaceId: string;
  colecao: { id: string; nome: string };
  papel?: string;
  documentos: DocumentoResumo[];
  envios: EnvioResumo[];
  estado?: "carregando" | "erro";
  onTentarNovamente?: () => void;
  onDocumentoApagado?: (id: string) => void;
  onEnvioRepetido?: (id: string) => void;
}

export default function AbasColecao({
  workspaceId,
  colecao,
  papel,
  documentos,
  envios,
  estado,
  onTentarNovamente,
  onDocumentoApagado,
  onEnvioRepetido,
}: AbasColecaoProps) {
  const pedida = useSearchParams().get("aba");
  const inicial: Aba = ABAS.some((aba) => aba.valor === pedida) ? (pedida as Aba) : "documentos";

  function aoMudar(valor: unknown) {
    const url = new URL(window.location.href);
    url.searchParams.set("aba", String(valor));
    window.history.replaceState(null, "", url);
  }

  return (
    <Tabs defaultValue={inicial} onValueChange={aoMudar}>
      <TabsList variant="line" aria-label={`Seções da coleção ${colecao.nome}`}>
        {ABAS.map((aba) => (
          <TabsTrigger key={aba.valor} value={aba.valor}>
            {aba.rotulo}
          </TabsTrigger>
        ))}
      </TabsList>
      <TabsContent value="documentos" className="min-w-0">
        <DataGridDocumentos
          workspaceId={workspaceId}
          colecaoId={colecao.id}
          documentos={documentos}
          papel={papel}
          estado={estado}
          onTentarNovamente={onTentarNovamente}
          onApagado={onDocumentoApagado}
        />
      </TabsContent>
      <TabsContent value="envios" className="min-w-0">
        <DataGridEnvios
          envios={envios}
          papel={papel}
          estado={estado}
          onTentarNovamente={onTentarNovamente}
          onRepetido={onEnvioRepetido}
        />
      </TabsContent>
      <TabsContent value="consulta" className="min-w-0">
        <ConsultaColecao colecaoId={colecao.id} />
      </TabsContent>
    </Tabs>
  );
}
