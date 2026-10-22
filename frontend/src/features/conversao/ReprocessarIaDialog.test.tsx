import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentType } from "react";
import { exigir } from "@/test/carregar";
import { apiJson } from "@/lib/api-client";
vi.mock("@/lib/api-client", () => ({ apiJson: vi.fn() }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
const props = {open:true,loteId:"l1",documento:{id:"d1",nome_arquivo:"original.pdf"},onReprocessado:vi.fn(),onOpenChange:vi.fn()};
async function montar() {
 const {default:Dialogo}=await exigir<{default:ComponentType<typeof props>}>("@/features/conversao/ReprocessarIaDialog");
 render(<Dialogo {...props}/>);
 return userEvent.setup();
}
it("informa envio ao provedor e só chama após confirmar",async()=>{
 // SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-021
 const usuario=await montar();
 expect(screen.getByText(/enviado ao provedor/i)).toBeInTheDocument();
 expect(apiJson).not.toHaveBeenCalled();
 vi.mocked(apiJson).mockResolvedValue({id:"l1",documentos:[]});
 await usuario.click(screen.getByRole("button",{name:"Confirmar reprocessamento"}));
 expect(apiJson).toHaveBeenCalledWith("/api/v1/conversoes/l1/documentos/d1/reprocessar-ia",{method:"POST"});
 expect(props.onReprocessado).toHaveBeenCalled();
});
it("cancelar não envia conteúdo",async()=>{
 // SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-022
 const usuario=await montar();
 await usuario.click(screen.getByRole("button",{name:"Cancelar"}));
 expect(apiJson).not.toHaveBeenCalled();
});
it("falha permanece no diálogo com mensagem segura",async()=>{
 // SPECSFY: SPEC-0036 US-005 FR-008 NFR-002 AC-023
 const usuario=await montar();
 vi.mocked(apiJson).mockRejectedValue(new Error("detalhe-interno"));
 await usuario.click(screen.getByRole("button",{name:"Confirmar reprocessamento"}));
 expect(screen.getByRole("alert")).toHaveTextContent(/não foi possível/i);
 expect(screen.queryByText(/detalhe-interno/)).not.toBeInTheDocument();
});
