"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { clearSession, hasSession } from "@/lib/session";

/**
 * Shell das telas autenticadas (SPEC-0013, seção 10).
 *
 * Sem sessão válida, qualquer rota redireciona para `/login`. O cabeçalho
 * traz a trilha (equipe → Projeto → tela) e a ação "Sair" sempre visível,
 * que limpa a sessão (AC-003). Não há menu lateral: a jornada é linear.
 *
 * `pronto` começa `false` no SSR e no primeiro render do cliente (evita
 * divergência de hidratação, já que `sessionStorage` não existe no servidor);
 * o efeito decide entre liberar o shell ou redirecionar ao Login.
 */
export default function LayoutAutenticado({
  children,
}: {
  children: ReactNode;
}) {
  const router = useRouter();
  const [pronto, setPronto] = useState(false);

  useEffect(() => {
    if (!hasSession()) {
      router.replace("/login");
      return;
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect -- detecção única de cliente
    setPronto(true);
  }, [router]);

  if (!pronto) {
    return null;
  }

  function sair() {
    clearSession();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="flex items-center justify-between border-b px-4 py-3">
        <nav aria-label="Trilha">
          <ol className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <li>Equipe</li>
            <li aria-hidden>/</li>
            <li className="text-foreground">Projeto</li>
          </ol>
        </nav>
        <Button variant="ghost" size="sm" onClick={sair}>
          Sair
        </Button>
      </header>
      <main className="flex-1 p-4">{children}</main>
    </div>
  );
}
