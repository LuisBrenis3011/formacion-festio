import { Sparkles } from "lucide-react";
import { ChatBubble } from "../components/chat-bubble";
import { ChatInput } from "../components/chat-input";
import { TypingIndicator } from "../components/typing-indicator";
import { SUGGESTIONS } from "../lib/constants";
import type { ChatMessage, ProveedorRecomendado } from "../types";

type ChatScreenProps = {
  messages: ChatMessage[];
  isPending: boolean;
  handleSend: (text: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  onSelectProvider: (provider: ProveedorRecomendado) => void;
  loadingDetail: boolean;
};

export function ChatScreen({
  messages,
  isPending,
  handleSend,
  messagesEndRef,
  onSelectProvider,
  loadingDetail,
}: ChatScreenProps) {
  return (
    <main className="chat-screen">
      {messages.length === 0 ? (
        <div className="chat-welcome">
          <div className="chat-welcome-icon">
            <Sparkles size={28} />
          </div>
          <h2>¡Hola! Soy el asistente de Festio</h2>
          <p>
            Cuéntame qué tipo de evento necesitas y te buscaré las mejores opciones
            con disponibilidad en tiempo real.
          </p>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              message={msg}
              onSelectProvider={onSelectProvider}
              loadingDetail={loadingDetail}
            />
          ))}
          {isPending && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      )}

      <ChatInput
        onSend={handleSend}
        isPending={isPending}
        suggestions={SUGGESTIONS}
        showSuggestions={messages.length === 0}
      />
    </main>
  );
}
