"use client";

import { useEffect, useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import DataGridBases, { type BaseResumo } from "@/features/bases/DataGridBases";
import UploadBaseSheet from "@/features/bases/UploadBaseSheet";
import { ApiError, apiJson } from "@/lib/api-client";

export default function ProjetoPage() {
  const [bases, setBases] = useState<BaseResumo[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [enviarAberto, setEnviarAberto] = useState(false);
  // Incrementado após um envio para forçar a releitura da listagem.
  const [releituras, setReleituras] = useState(0);

  useEffect(() => {
    let ativo = true;
    apiJson<BaseResumo[]>("/api/v1/bases")
      .then((dados) => {
        if (ativo) {
          setBases(dados);
          setErro(null);
        }
      })
      .catch((causa) => {
        // 401 já leva ao Login pelo api-client; aqui é só falha de leitura.
        if (ativo && !(causa instanceof ApiError && causa.unauthorized)) {
          setErro("Não foi possível carregar as bases. Tente novamente.");
        }
      })
      .finally(() => {
        if (ativo) setCarregando(false);
      });
    return () => {
      ativo = false;
    };
  }, [releituras]);

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Bases do projeto"
        description="Envie bases Markdown e acompanhe a indexação de cada uma."
        actions={
          <Button type="button" onClick={() => setEnviarAberto(true)}>
            Enviar base
          </Button>
        }
      />

      {erro ? (
        <Alert variant="destructive">
          <AlertDescription>{erro}</AlertDescription>
        </Alert>
      ) : null}

      <DataGridBases bases={bases} carregando={carregando} />

      <UploadBaseSheet
        open={enviarAberto}
        onOpenChange={setEnviarAberto}
        onCreated={() => {
          setEnviarAberto(false);
          setCarregando(true);
          setReleituras((valor) => valor + 1);
        }}
      />
    </div>
  );
}
