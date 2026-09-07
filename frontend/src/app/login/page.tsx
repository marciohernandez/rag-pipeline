import type { Metadata } from "next";

import LoginForm from "@/features/auth/LoginForm";

export const metadata: Metadata = {
  title: "Entrar — RAG Pipeline",
};

export default function LoginPage() {
  return (
    <main className="flex min-h-dvh items-center justify-center p-6">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <div className="flex flex-col gap-1.5">
          <h1 className="text-lg font-semibold">Entrar</h1>
          <p className="text-sm text-muted-foreground">
            Use um token de demonstração para acompanhar o projeto.
          </p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
