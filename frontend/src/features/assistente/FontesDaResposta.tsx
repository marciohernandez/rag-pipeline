import Link from "next/link";

import { Badge } from "@/components/ui/badge";

import type { FonteDaResposta } from "./useAssistente";

/**
 * Fontes de uma resposta do assistente (SPEC-0031, FR-008 / NFR-003).
 *
 * Fonte estruturada vira link para a coleção, o documento ou o envio, com rótulo
 * acessível que diz o destino ("Abrir documento X da coleção Y"); fonte em texto
 * simples, de respostas antigas ou da documentação do produto, continua um `Badge`
 * sem link. A lista quebra linha e nunca estoura a largura do painel.
 */

const SEPARADOR = " — ";

function nomeDaColecao(rotulo: string): string {
  const partes = rotulo.split(SEPARADOR);
  return partes.length > 1 ? partes.slice(1).join(SEPARADOR) : rotulo;
}

function minuscula(texto: string): string {
  return texto.charAt(0).toLowerCase() + texto.slice(1);
}

export function rotuloAcessivel(fonte: FonteDaResposta): string {
  if (fonte.tipo === "documento" && fonte.documento) {
    return `Abrir documento ${fonte.documento} da coleção ${nomeDaColecao(fonte.rotulo)}`;
  }
  if (fonte.tipo === "colecao") return `Abrir coleção ${fonte.rotulo}`;
  return `Abrir ${minuscula(fonte.rotulo)}`;
}

const CLASSE_DA_FONTE = "h-auto min-h-5 max-w-full py-0.5 [overflow-wrap:anywhere] whitespace-normal";

export default function FontesDaResposta({ fontes }: { fontes: (FonteDaResposta | string)[] }) {
  if (fontes.length === 0) return null;
  return (
    <ul aria-label="Fontes citadas" className="flex max-w-[92%] flex-wrap gap-1">
      {fontes.map((fonte, indice) => (
        <li key={typeof fonte === "string" ? `${fonte}-${indice}` : `${fonte.rota}-${fonte.rotulo}`} className="min-w-0">
          {typeof fonte === "string" ? (
            <Badge variant="outline" className={CLASSE_DA_FONTE}>
              {fonte}
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className={CLASSE_DA_FONTE}
              render={<Link href={fonte.rota} aria-label={rotuloAcessivel(fonte)} />}
            >
              {fonte.rotulo}
            </Badge>
          )}
        </li>
      ))}
    </ul>
  );
}
