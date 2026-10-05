import { scriptTema } from "@/lib/tema";

export default function ScriptTema() {
  return (
    <script
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: scriptTema() }}
    />
  );
}
