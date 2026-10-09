"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import BarraEtapas from "@/features/ingestao/BarraEtapas";
import EtapaArquivos from "@/features/ingestao/EtapaArquivos";
import EtapaDivisao from "@/features/ingestao/EtapaDivisao";
import EtapaPrevia from "@/features/ingestao/EtapaPrevia";
import EtapaPublicacao from "@/features/ingestao/EtapaPublicacao";
import { ETAPAS, useFluxoIngestao } from "@/features/ingestao/useFluxoIngestao";
import { TAMANHOS_DE_PAGINA, validarDivisao } from "@/lib/ingestao";
import { seletor } from "@/features/ingestao/seletor";

const AVISO_SAIDA = "Sair sem publicar? Os arquivos e as configurações desta Base serão descartados.";

/**
 * Fluxo de nova Base em quatro etapas (SPEC-0026): Arquivos, Divisão, Prévia e
 * Publicação. Nada é guardado no servidor antes de publicar; sair ou recarregar
 * descarta tudo, com aviso quando há alterações pendentes.
 */
export default function FluxoIngestao({ workspaceId }: { workspaceId: string }) {
  const fluxo = useFluxoIngestao(workspaceId);
  const { etapa, pendente } = fluxo;
  const titulo = useRef<HTMLHeadingElement>(null);
  const primeira = useRef(true);
  const [tentativasDivisao, setTentativasDivisao] = useState(0);
  const indice = ETAPAS.findIndex((e) => e.id === etapa);

  useEffect(() => {
    if (primeira.current) {
      primeira.current = false;
      return;
    }
    titulo.current?.focus();
  }, [etapa]);

  useEffect(() => {
    if (!pendente) return;
    function aoFechar(evento: BeforeUnloadEvent) {
      evento.preventDefault();
      evento.returnValue = "";
    }
    function aoNavegar(evento: MouseEvent) {
      const ancora = (evento.target as HTMLElement | null)?.closest?.("a[href]");
      const destino = ancora?.getAttribute("href") ?? "";
      if (!ancora || !destino.startsWith("/") || ancora.getAttribute("target") === "_blank") return;
      if (!window.confirm(AVISO_SAIDA)) {
        evento.preventDefault();
        evento.stopPropagation();
      }
    }
    window.addEventListener("beforeunload", aoFechar);
    document.addEventListener("click", aoNavegar, true);
    return () => {
      window.removeEventListener("beforeunload", aoFechar);
      document.removeEventListener("click", aoNavegar, true);
    };
  }, [pendente]);

  function avancar() {
    if (etapa === "divisao") {
      const erros = validarDivisao(fluxo.tamanho, fluxo.overlap, fluxo.padroes.limites, fluxo.splitter, fluxo.processamento);
      if (erros.tamanho || erros.overlap || erros.separador) {
        setTentativasDivisao((valor) => valor + 1);
        return;
      }
    }
    fluxo.ir(ETAPAS[indice + 1].id);
  }

  const podeAvancar =
    etapa === "arquivos"
      ? pendente
      : etapa === "previa"
        ? fluxo.previa !== null && fluxo.previa.resumo.chunks > 0 && !fluxo.calculando
        : etapa === "divisao";

  return (
    <div className="flex flex-col gap-5">
      <BarraEtapas etapa={etapa} maisAlta={fluxo.maisAlta} onIr={fluxo.ir} />
      <section className="flex flex-col gap-4 rounded-lg border p-4">
        <h2 ref={titulo} tabIndex={-1} className="text-base font-semibold outline-none">
          {ETAPAS[indice].titulo}
        </h2>
        {etapa === "arquivos" ? (
          <EtapaArquivos
            arquivos={fluxo.arquivos}
            usarPreparada={fluxo.usarPreparada}
            onAdicionar={fluxo.adicionarArquivos}
            onRemover={fluxo.removerArquivo}
            onPreparada={fluxo.alternarPreparada}
          />
        ) : null}
        {etapa === "divisao" ? (
          <EtapaDivisao
            arquivos={fluxo.arquivos}
            padroes={fluxo.padroes}
            splitter={fluxo.splitter}
            tamanho={fluxo.tamanho}
            overlap={fluxo.overlap}
            tentativas={tentativasDivisao}
            onAlterar={fluxo.alterarDivisao}
            processamento={fluxo.processamento}
            onAlterarProcessamento={fluxo.alterarProcessamento}
          />
        ) : null}
        {etapa === "previa" ? (
          <div
            role="toolbar"
            aria-label="Ações da Prévia"
            className="sticky top-0 z-10 -mx-4 flex flex-wrap items-center justify-between gap-3 border-b bg-background/95 px-4 py-2 backdrop-blur"
          >
            <Button type="button" variant="outline" onClick={() => fluxo.ir(ETAPAS[indice - 1].id)}>
              Voltar
            </Button>
            <div className="flex items-center gap-2">
              <label htmlFor="previa-tamanho-pagina" className="text-sm text-muted-foreground">
                Chunks por página
              </label>
              <select
                id="previa-tamanho-pagina"
                value={fluxo.tamanhoPagina}
                onChange={(e) => fluxo.alterarTamanhoPagina(Number(e.target.value))}
                className={`${seletor} w-20`}
              >
                {TAMANHOS_DE_PAGINA.map((valor) => (
                  <option key={valor} value={valor}>
                    {valor}
                  </option>
                ))}
              </select>
            </div>
            <Button type="button" disabled={!podeAvancar} onClick={avancar}>
              Próxima
            </Button>
          </div>
        ) : null}
        {etapa === "previa" ? (
          <EtapaPrevia
            tamanhoPagina={fluxo.tamanhoPagina}
            previa={fluxo.previa}
            calculando={fluxo.calculando}
            erro={fluxo.erroPrevia}
            documento={fluxo.documento}
            documentos={fluxo.arquivos.map((arquivo) => arquivo.name)}
            onCalcular={fluxo.calcularPrevia}
          />
        ) : null}
        {etapa === "publicacao" ? (
          <EtapaPublicacao
            resumo={{
              arquivos: fluxo.usarPreparada ? (fluxo.previa?.resumo.documentos ?? 0) : fluxo.arquivos.length,
              chunks: fluxo.previa?.resumo.chunks ?? 0,
            }}
            onPublicar={fluxo.publicar}
          />
        ) : null}
        {etapa === "previa" ? null : (
        <div className="flex items-center justify-between gap-3 border-t pt-4">
          <Button type="button" variant="outline" disabled={indice === 0} onClick={() => fluxo.ir(ETAPAS[indice - 1].id)}>
            Voltar
          </Button>
          {etapa !== "publicacao" ? (
            <Button type="button" disabled={!podeAvancar} onClick={avancar}>
              Próxima
            </Button>
          ) : null}
        </div>
        )}
      </section>
    </div>
  );
}
