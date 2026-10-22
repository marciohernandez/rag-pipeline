import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import ConversaoSheet from "@/features/conversao/ConversaoSheet";
import { apiJson } from "@/lib/api-client";
vi.mock("@/lib/api-client", () => ({ apiJson: vi.fn() }));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
it("exibe limites pequenos vindos da API sem arredondar para zero",async()=>{
 // SPECSFY: SPEC-0036 US-004 FR-006 NFR-005 AC-018
 vi.mocked(apiJson).mockResolvedValue({max_arquivos:3,max_bytes_arquivo:700,max_bytes_lote:900});
 render(<ConversaoSheet open workspaceId="w1" papel="owner" />);
 expect(await screen.findByText(/700 bytes por arquivo/)).toBeInTheDocument();
 expect(screen.getByText(/900 bytes por lote e 3 documentos/)).toBeInTheDocument();
});
