import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  type Ocorrencia,
  rotuloEtiqueta,
  varianteEtiqueta,
} from "@/features/contradicoes/situacaoContradicao";

/**
 * Cartão de uma contradição (SPEC-0038, FR-004 / FR-007): assunto, etiqueta, trechos lado a
 * lado (empilhados no celular), arquivo de origem de cada um e a explicação.
 */
interface CartaoOcorrenciaProps {
  ocorrencia: Ocorrencia;
  /** Arquivos corrigidos pela decisão da empresa (SPEC-0039); mostra o selo e o link. */
  corrigidoEm?: string[];
  onVerVersoes?: (arquivo: string) => void;
}

export default function CartaoOcorrencia({
  ocorrencia,
  corrigidoEm,
  onVerVersoes,
}: CartaoOcorrenciaProps) {
  return (
    <article className="flex min-w-0 flex-col gap-3 rounded-lg border bg-card p-4">
      <header className="flex flex-wrap items-center gap-2">
        <h3 className="min-w-0 text-base font-medium [overflow-wrap:anywhere]">
          {ocorrencia.assunto}
        </h3>
        <Badge variant={varianteEtiqueta(ocorrencia.etiqueta)}>
          {rotuloEtiqueta(ocorrencia.etiqueta)}
        </Badge>
        {ocorrencia.impacto === "alto" ? <Badge variant="outline">Impacto alto</Badge> : null}
        {corrigidoEm && corrigidoEm.length > 0 ? <Badge variant="secondary">Corrigido</Badge> : null}
      </header>
      <div data-testid="trechos-lado-a-lado" className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {ocorrencia.trechos.map((trecho, indice) => (
          <figure key={`${trecho.arquivo}-${indice}`} className="flex min-w-0 flex-col gap-1">
            <figcaption className="flex flex-wrap items-center gap-2 text-sm font-medium">
              <span className="break-words">{trecho.arquivo}</span>
              {trecho.arquivo === ocorrencia.arquivo_mais_antigo ? (
                <Badge variant="secondary">Mais antigo</Badge>
              ) : null}
            </figcaption>
            <blockquote className="break-words rounded-md bg-muted p-3 text-sm [overflow-wrap:anywhere]">
              {trecho.texto}
            </blockquote>
            {trecho.imagem ? (
              <span className="break-words text-xs text-muted-foreground">
                Imagem de origem: {trecho.imagem}
              </span>
            ) : null}
          </figure>
        ))}
      </div>
      <p className="break-words text-sm text-muted-foreground">{ocorrencia.explicacao}</p>
      {onVerVersoes && corrigidoEm
        ? corrigidoEm.map((arquivo) => (
            <Button
              key={arquivo}
              type="button"
              variant="link"
              size="sm"
              className="h-auto min-w-0 justify-start p-0 whitespace-normal break-words"
              onClick={() => onVerVersoes(arquivo)}
            >
              Ver versões de {arquivo}
            </Button>
          ))
        : null}
    </article>
  );
}
