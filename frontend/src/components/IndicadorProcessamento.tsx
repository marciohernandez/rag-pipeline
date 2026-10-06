import type { ReactNode } from "react";
import { cn } from "cn";

import { Spinner } from "@/components/ui/spinner";

/** Feedback local para uma área de dados; mantém o texto acessível e o ícone decorativo. */
export function IndicadorProcessamento({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span role="status" aria-live="polite" aria-label={typeof children === "string" ? children : undefined} className={cn("inline-flex items-center gap-2 text-sm text-muted-foreground", className)}>
      <Spinner aria-hidden="true" />
      <span>{children}</span>
    </span>
  );
}
