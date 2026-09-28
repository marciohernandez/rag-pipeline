"use client";

import { useCallback, useRef, useState } from "react";

import { ApiError, apiJson } from "@/lib/api-client";

/**
 * Estado e chamadas do assistente (SPEC-0021, US-001 / US-002 / FR-002 / FR-003).
 *
 * Usa somente o cliente HTTP único. Falha ao enviar nunca descarta o texto da
 * pessoa: `enviar` devolve `false` e o chamador preserva o campo para reenvio.
 * Um 401 já limpou a sessão no cliente; aqui só avisamos o shell.
 */

export interface MensagemAssistente {
  id: string;
  papel: "pessoa" | "assistente";
  conteudo: string;
  fontes: string[];
  base_id: string | null;
  criada_em: string;
}

export interface ConversaResumo {
  id: string;
  titulo: string;
  atualizada_em: string;
}

interface ConversaDetalhe {
  id: string;
  titulo: string;
  mensagens: MensagemAssistente[];
}

interface RespostaEnvio {
  mensagem_pessoa: MensagemAssistente;
  mensagem_assistente: MensagemAssistente;
}

const BASE = "/api/v1/assistente";
export const ERRO_DE_ENVIO = "Não foi possível obter a resposta agora. Tente novamente.";
export const ERRO_DE_HISTORICO = "Não foi possível carregar suas conversas. Tente novamente.";

export interface OpcoesAssistente {
  onSessaoEncerrada?: () => void;
}

export function useAssistente({ onSessaoEncerrada }: OpcoesAssistente = {}) {
  const [conversaId, setConversaId] = useState<string | null>(null);
  const [mensagens, setMensagens] = useState<MensagemAssistente[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [conversas, setConversas] = useState<ConversaResumo[]>([]);
  const [carregandoConversas, setCarregandoConversas] = useState(false);
  const [erroHistorico, setErroHistorico] = useState<string | null>(null);
  const contador = useRef(0);

  const tratarFalha = useCallback(
    (falha: unknown, mensagem: string, definir: (texto: string) => void) => {
      if (falha instanceof ApiError && falha.unauthorized) {
        onSessaoEncerrada?.();
        return;
      }
      definir(mensagem);
    },
    [onSessaoEncerrada],
  );

  const carregarHistorico = useCallback(async () => {
    setCarregandoConversas(true);
    setErroHistorico(null);
    try {
      setConversas(await apiJson<ConversaResumo[]>(`${BASE}/conversas`));
    } catch (falha) {
      tratarFalha(falha, ERRO_DE_HISTORICO, setErroHistorico);
    } finally {
      setCarregandoConversas(false);
    }
  }, [tratarFalha]);

  const abrirConversa = useCallback(
    async (id: string): Promise<boolean> => {
      setErro(null);
      try {
        const detalhe = await apiJson<ConversaDetalhe>(`${BASE}/conversas/${encodeURIComponent(id)}`);
        setConversaId(detalhe.id);
        setMensagens(detalhe.mensagens);
        return true;
      } catch (falha) {
        tratarFalha(falha, ERRO_DE_HISTORICO, setErro);
        return false;
      }
    },
    [tratarFalha],
  );

  const novaConversa = useCallback(() => {
    setConversaId(null);
    setMensagens([]);
    setErro(null);
  }, []);

  const enviar = useCallback(
    async (texto: string, baseId: string | null): Promise<boolean> => {
      contador.current += 1;
      const provisoria: MensagemAssistente = {
        id: `pendente-${contador.current}`,
        papel: "pessoa",
        conteudo: texto,
        fontes: [],
        base_id: baseId,
        criada_em: new Date().toISOString(),
      };
      setEnviando(true);
      setErro(null);
      setMensagens((atuais) => [...atuais, provisoria]);
      try {
        let destino = conversaId;
        if (destino === null) {
          const criada = await apiJson<{ id: string }>(`${BASE}/conversas`, { method: "POST" });
          destino = criada.id;
          setConversaId(destino);
        }
        const resposta = await apiJson<RespostaEnvio>(
          `${BASE}/conversas/${encodeURIComponent(destino)}/mensagens`,
          {
            method: "POST",
            headers: { "content-type": "application/json" },
            body: JSON.stringify({ texto, base_id: baseId }),
          },
        );
        setMensagens((atuais) => [
          ...atuais.filter((m) => m.id !== provisoria.id),
          resposta.mensagem_pessoa,
          resposta.mensagem_assistente,
        ]);
        return true;
      } catch (falha) {
        setMensagens((atuais) => atuais.filter((m) => m.id !== provisoria.id));
        tratarFalha(falha, ERRO_DE_ENVIO, setErro);
        return false;
      } finally {
        setEnviando(false);
      }
    },
    [conversaId, tratarFalha],
  );

  const apagar = useCallback(
    async (id: string): Promise<boolean> => {
      try {
        await apiJson(`${BASE}/conversas/${encodeURIComponent(id)}`, { method: "DELETE" }).catch(
          (falha: unknown) => {
            // 204 sem corpo não é JSON: só falhas HTTP contam como erro.
            if (falha instanceof ApiError) throw falha;
          },
        );
        setConversas((atuais) => atuais.filter((c) => c.id !== id));
        if (id === conversaId) novaConversa();
        return true;
      } catch (falha) {
        tratarFalha(falha, ERRO_DE_HISTORICO, setErroHistorico);
        return false;
      }
    },
    [conversaId, novaConversa, tratarFalha],
  );

  return {
    conversaId,
    mensagens,
    enviando,
    erro,
    conversas,
    carregandoConversas,
    erroHistorico,
    carregarHistorico,
    abrirConversa,
    novaConversa,
    enviar,
    apagar,
  };
}
