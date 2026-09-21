import { permanentRedirect } from "next/navigation";

/** Link antigo preservado como redirect permanente (SPEC-0019, DEC-005). */
export default function ProjetoPage() {
  permanentRedirect("/workspaces");
  return null;
}
