"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDownIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import TrocarSenhaDialog from "@/features/auth/TrocarSenhaDialog";
import { apiFetch } from "@/lib/api-client";
import { clearSession } from "@/lib/session";

export default function MenuPessoa({ nome, papel }: { nome: string; papel: string }) {
  const router = useRouter();
  const [trocarSenha, setTrocarSenha] = useState(false);

  async function sair() {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // O encerramento local continua mesmo se a sessão remota já terminou.
    }
    clearSession();
    router.replace("/login");
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger render={<Button variant="ghost" size="sm" />}>
          <span className="max-w-40 truncate">{nome}</span>
          <span className="sr-only">, papel {papel}</span>
          <ChevronDownIcon aria-hidden />
        </DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={() => setTrocarSenha(true)}>Trocar senha</DropdownMenuItem>
          <DropdownMenuItem onClick={() => void sair()}>Sair</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <TrocarSenhaDialog open={trocarSenha} onOpenChange={setTrocarSenha} />
    </>
  );
}
