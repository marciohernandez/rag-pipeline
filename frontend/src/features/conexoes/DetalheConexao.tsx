import DetailLists from "@/components/DetailLists";
import { rotulosTipo, type ConexaoResumo } from "@/features/conexoes/DataGridConexoes";

function data(iso?: string | null) {
  if (!iso) return "—";
  const valor = new Date(iso);
  return Number.isNaN(valor.getTime()) ? iso : valor.toLocaleString("pt-BR");
}

/** Detalhe somente leitura de uma conexão; a chave aparece apenas mascarada. */
export default function DetalheConexao({ conexao }: { conexao: ConexaoResumo }) {
  const config = conexao.configuracao ?? {};
  const itens = [
    { label: "Tipo", value: rotulosTipo[conexao.tipo] ?? conexao.tipo },
    { label: "Situação", value: conexao.situacao === "ativa" ? "Ativa" : "Desativada" },
    ...(conexao.tipo === "embeddings_openai"
      ? [
          { label: "Modelo", value: config.modelo ?? "—" },
          { label: "Dimensões", value: config.dimensoes ?? "—" },
          { label: "URL base", value: config.url_base ?? "Padrão do provedor" },
        ]
      : [{ label: "URL", value: config.url ?? "—" }]),
    { label: "Chave", value: conexao.segredo_definido ? conexao.segredo_mascara : "Sem chave" },
    { label: "Bases que usam esta conexão", value: conexao.em_uso },
    { label: "Criada em", value: data(conexao.criado_em) },
    { label: "Atualizada em", value: data(conexao.atualizada_em) },
  ];
  return <DetailLists items={itens} />;
}
