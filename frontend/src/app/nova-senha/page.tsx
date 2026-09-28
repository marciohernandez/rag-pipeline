"use client";

import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import NovaSenhaForm from "@/features/auth/NovaSenhaForm";
import { apiFetch } from "@/lib/api-client";
import { clearSession } from "@/lib/session";

export default function NovaSenhaPage() {
  const router = useRouter();

  async function sair() {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // A sessão local deve terminar mesmo se já tiver expirado no servidor.
    }
    clearSession();
    router.replace("/login");
  }

  return (
    <main className="flex min-h-dvh items-center justify-center p-4 sm:p-6">
      <section className="flex w-full max-w-md flex-col gap-6 rounded-xl border bg-card p-5 shadow-sm sm:p-7">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold">Defina sua nova senha</h1>
            <p className="mt-1 text-sm text-muted-foreground">Sua senha foi definida por outra pessoa. Troque-a antes de continuar.</p>
          </div>
          <Button type="button" variant="ghost" onClick={() => void sair()}>Sair</Button>
        </div>
        <NovaSenhaForm />
      </section>
    </main>
  );
}
