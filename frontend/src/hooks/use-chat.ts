import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRecomendarEvento } from "./use-recomendar";
import { readError } from "../lib/format";
import type { ChatMessage, RecomendacionRequest } from "../types";

let messageIdCounter = 0;
function nextId() {
  return `msg-${++messageIdCounter}-${Date.now()}`;
}

/**
 * Encapsulates all chat state: messages, auto-scroll, and the
 * send handler that builds historial and calls the recommendation mutation.
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationState, setConversationState] = useState<RecomendacionRequest | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const searchMutation = useRecomendarEvento();
  const latestRecommendation = useMemo(() => {
    for (let index = messages.length - 1; index >= 0; index -= 1) {
      const recommendation = messages[index].recommendation;
      if (recommendation) return recommendation;
    }
    return null;
  }, [messages]);

  // Auto-scroll to bottom when messages change or mutation is pending
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, searchMutation.isPending]);

  const handleSend = useCallback(
    (text: string) => {
      const userMessage: ChatMessage = {
        id: nextId(),
        role: "user",
        content: text,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);

      // Build historial from current messages + this new one
      const historial = [...messages, userMessage].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      searchMutation.mutate(
        { mensaje: text, historial, estado_conversacion: conversationState },
        {
          onSuccess: (data) => {
            setConversationState(data.estado_conversacion ?? conversationState);
            setMessages((prev) => [
              ...prev,
              {
                id: nextId(),
                role: "assistant" as const,
                content: data.respuesta,
                recommendation: data,
                timestamp: new Date(),
              },
            ]);
          },
          onError: (err) => {
            setMessages((prev) => [
              ...prev,
              {
                id: nextId(),
                role: "assistant" as const,
                content: `Lo siento, ocurrió un error: ${readError(err)}. ¿Podrías intentarlo de nuevo?`,
                timestamp: new Date(),
              },
            ]);
          },
        },
      );
    },
    [conversationState, messages, searchMutation],
  );

  const resetChat = useCallback(() => {
    setMessages([]);
    setConversationState(null);
  }, []);

  return {
    messages,
    isPending: searchMutation.isPending,
    handleSend,
    messagesEndRef,
    latestRecommendation,
    resetChat,
  };
}
