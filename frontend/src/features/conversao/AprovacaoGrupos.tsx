"use client";

import { useState } from "react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import CartaoGrupoImagens, {
  type GrupoProposto,
} from "@/features/conversao/CartaoGrupoImagens";
import { ApiError, apiJson } from "@/lib/api-client";

const MENSAGEM_FALHA = "Não foi possível confirmar os grupos. Tente novamente.";

export interface PropostaDeGrupos {
  certeza: "total" | "incerta";
  grupos: GrupoProposto[];
}

interface AprovacaoGruposProps {
  loteId: string;
  proposta: PropostaDeGrupos;
  podeEscrever: boolean;
  onConfirmada?: () => void;
}

function renumerar(grupos: GrupoProposto[]): GrupoProposto[] {
  return grupos
    .filter((grupo) => grupo.imagens.length > 0)
    .map((grupo, indice) => ({
      ...grupo,
      ordem: indice + 1,
      imagens: grupo.imagens.map((imagem, posicao) => ({ ...imagem, posicao: posicao + 1 })),
    }));
}

/**
 * Passo "Aprovar grupos" do lote de conversão (SPEC-0040, FR-002 / FR-007): a pessoa confere a
 * proposta, move e reordena imagens e confirma; nada é gerado antes disso. Com certeza total os
 * grupos vêm pré-aprovados e um clique basta. O member vê tudo em modo leitura.
 */
export default function AprovacaoGrupos({
  loteId,
  proposta,
  podeEscrever,
  onConfirmada,
}: AprovacaoGruposProps) {
  const [grupos, setGrupos] = useState<GrupoProposto[]>(proposta.grupos);
  const [alterado, setAlterado] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmado, setConfirmado] = useState(false);
  const base = `/api/v1/conversoes/${encodeURIComponent(loteId)}/grupos`;

  function atualizar(proximo: GrupoProposto[]) {
    setGrupos(renumerar(proximo));
    setAlterado(true);
  }

  function mover(documentoId: string, destinoId: string) {
    const imagem = grupos.flatMap((g) => g.imagens).find((i) => i.documento_id === documentoId);
    if (!imagem) return;
    atualizar(
      grupos.map((grupo) => {
        if (grupo.id === destinoId) return { ...grupo, aprovado: false, imagens: [...grupo.imagens, imagem] };
        return {
          ...grupo,
          aprovado: false,
          imagens: grupo.imagens.filter((i) => i.documento_id !== documentoId),
        };
      }),
    );
  }

  function reordenar(documentoId: string, direcao: "subir" | "descer") {
    atualizar(
      grupos.map((grupo) => {
        const indice = grupo.imagens.findIndex((i) => i.documento_id === documentoId);
        if (indice < 0) return grupo;
        const alvo = direcao === "subir" ? indice - 1 : indice + 1;
        if (alvo < 0 || alvo >= grupo.imagens.length) return grupo;
        const imagens = [...grupo.imagens];
        [imagens[indice], imagens[alvo]] = [imagens[alvo], imagens[indice]];
        return { ...grupo, aprovado: false, imagens };
      }),
    );
  }

  async function confirmar() {
    if (enviando) return;
    setEnviando(true);
    setErro(null);
    try {
      if (alterado) {
        await apiJson(base, {
          method: "PUT",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({
            grupos: grupos.map((g) => ({ imagens: g.imagens.map((i) => i.documento_id) })),
          }),
        });
      }
      await apiJson(`${base}/confirmar`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({}),
      });
      setConfirmado(true);
      onConfirmada?.();
    } catch (causa) {
      setErro(causa instanceof ApiError && causa.detail ? causa.detail : MENSAGEM_FALHA);
    } finally {
      setEnviando(false);
    }
  }

  const incerta = proposta.certeza !== "total" || alterado;

  return (
    <section aria-label="Aprovar grupos" className="flex min-w-0 flex-col gap-3">
      {podeEscrever ? (
        incerta ? (
          <Alert>
            <AlertDescription>
              Confira cada grupo e a ordem das imagens antes de confirmar: a proposta não tem
              certeza total.
            </AlertDescription>
          </Alert>
        ) : (
          <p className="text-sm text-muted-foreground">
            Certeza total: nome, data e pasta concordam. Um clique em Confirmar grupos basta.
          </p>
        )
      ) : (
        <Alert role="status">
          <AlertDescription>
            A aprovação dos grupos cabe a owner ou admin. Você pode conferir a proposta abaixo.
          </AlertDescription>
        </Alert>
      )}
      <div data-testid="lista-grupos" className="flex min-w-0 flex-col gap-3">
        {grupos.map((grupo) => (
          <CartaoGrupoImagens
            key={grupo.id}
            loteId={loteId}
            grupo={grupo}
            outrosGrupos={grupos.filter((g) => g.id !== grupo.id).map((g) => ({ id: g.id, ordem: g.ordem }))}
            somenteLeitura={!podeEscrever}
            onMover={mover}
            onReordenar={reordenar}
          />
        ))}
      </div>
      {erro ? (
        <Alert variant="destructive">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
            <span>{erro}</span>
            <Button type="button" variant="outline" size="sm" onClick={confirmar}>
              Tentar novamente
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}
      {confirmado ? (
        <p role="status" aria-live="polite" className="text-sm">
          Grupos confirmados. Gerando os documentos…
        </p>
      ) : null}
      {podeEscrever ? (
        <div
          data-testid="rodape-aprovacao"
          className="sticky bottom-0 flex flex-col gap-2 border-t bg-background py-3 sm:flex-row sm:justify-end"
        >
          <Button type="button" onClick={confirmar} disabled={enviando || confirmado} aria-busy={enviando}>
            Confirmar grupos
          </Button>
        </div>
      ) : null}
    </section>
  );
}
