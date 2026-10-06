"use client";

import { useId } from "react";
import {
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { useTema } from "@/features/tema/useTema";
import { normalizarPreferencia } from "@/lib/tema";

export default function SeletorTema() {
  const id = useId();
  const { preferencia, escolher } = useTema();

  return (
    <DropdownMenuRadioGroup
      aria-labelledby={id}
      value={preferencia}
      onValueChange={(valor: unknown) => escolher(normalizarPreferencia(valor))}
    >
      <DropdownMenuLabel id={id}>Tema</DropdownMenuLabel>
      <DropdownMenuRadioItem value="claro">Claro</DropdownMenuRadioItem>
      <DropdownMenuRadioItem value="escuro">Escuro</DropdownMenuRadioItem>
      <DropdownMenuRadioItem value="sistema">Sistema</DropdownMenuRadioItem>
    </DropdownMenuRadioGroup>
  );
}
