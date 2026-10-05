"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronDownIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import SeletorTema from "@/features/tema/SeletorTema";
import TrocarSenhaDialog from "@/features/auth/TrocarSenhaDialog";
import { apiFetch } from "@/lib/api-client";
import { clearSession, type PessoaSessao } from "@/lib/session";

const rotulosPapel: Record<PessoaSessao["papel"], string> = {
  owner: "Owner",
  admin: "Admin",
  member: "Member",
};

export default function MenuPessoa({ nome, papel }: { nome: string; papel: PessoaSessao["papel"] }) {
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
          <span className="sr-only">, papel {rotulosPapel[papel]}</span>
          <ChevronDownIcon aria-hidden />
        </DropdownMenuTrigger>
        <DropdownMenuContent keepMounted>
          <DropdownMenuGroup>
            <DropdownMenuLabel className="flex max-w-64 flex-col gap-0.5">
              <span className="truncate text-sm font-medium text-popover-foreground">{nome}</span>
              <span>{rotulosPapel[papel]}</span>
            </DropdownMenuLabel>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <SeletorTema />
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setTrocarSenha(true)}>Trocar senha</DropdownMenuItem>
          <DropdownMenuItem onClick={() => void sair()}>Sair</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <TrocarSenhaDialog open={trocarSenha} onOpenChange={setTrocarSenha} />
    </>
  );
}
