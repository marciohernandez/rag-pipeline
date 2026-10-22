"use client";

import { useParams } from "next/navigation";

import RelatorioContradicoes from "@/features/contradicoes/RelatorioContradicoes";

export default function ContradicoesDaColecaoPage() {
  const { id, colecaoId } = useParams<{ id: string; colecaoId: string }>();
  return <RelatorioContradicoes colecaoId={colecaoId} workspaceId={id} />;
}
