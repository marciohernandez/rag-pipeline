"use client";

import "./globals.css";

/** Última fronteira de erro do App Router, inclusive quando o layout falha. */
export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt-BR">
      <body className="flex min-h-dvh items-center justify-center bg-background p-4 text-foreground">
        <main className="flex w-full max-w-md flex-col gap-4 rounded-lg border bg-card p-6 shadow-sm">
          <div className="flex flex-col gap-1">
            <h1 className="text-lg font-semibold">Não foi possível abrir esta tela</h1>
            <p className="text-sm text-muted-foreground">
              Tente novamente. Se o problema continuar, volte para os Workspaces.
            </p>
          </div>
          <button
            type="button"
            className="inline-flex h-8 w-fit items-center justify-center rounded-lg bg-primary px-3 text-sm font-medium text-primary-foreground focus-visible:outline-2 focus-visible:outline-ring"
            onClick={reset}
          >
            Tentar novamente
          </button>
        </main>
      </body>
    </html>
  );
}
