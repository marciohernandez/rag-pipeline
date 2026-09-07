import type { ReactNode } from "react";

/**
 * Cabeçalho único das telas autenticadas (SPEC-0013, seção 10).
 *
 * A mesma implementação serve a tela Projeto (lista) e a tela Detalhe da
 * execução; as variações entram por props (`description`, `actions`, `status`).
 * Não replicar este markup por página.
 */
interface PageHeaderProps {
  title: string;
  description?: string;
  status?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({
  title,
  description,
  status,
  actions,
}: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <h1 className="text-lg font-semibold">{title}</h1>
          {status}
        </div>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex items-center gap-2">{actions}</div>
      ) : null}
    </div>
  );
}
