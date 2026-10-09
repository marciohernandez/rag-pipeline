/**
 * Lista dos chunks-fontes de uma consulta (SPEC-0013, US-004 / AC-012 / AC-018; SPEC-0030).
 *
 * Cada trecho é identificado pelo documento de origem em texto — nunca só por
 * cor —, para leitura assistiva e para daltônicos.
 */

export interface ChunkFonte {
  documento: string | null;
  trecho: string;
}

export default function ChunksFontes({ chunks }: { chunks: ChunkFonte[] }) {
  if (chunks.length === 0) {
    return null;
  }
  return (
    <section className="flex flex-col gap-2">
      <h3 className="text-sm font-medium">Chunks-fontes</h3>
      <ul className="flex flex-col gap-2">
        {chunks.map((chunk, indice) => (
          <li key={indice} className="rounded-md border p-3 text-sm">
            <p className="font-mono text-xs text-muted-foreground">
              Fonte: {chunk.documento ?? "documento não identificado"}
            </p>
            <p className="mt-1">{chunk.trecho}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
