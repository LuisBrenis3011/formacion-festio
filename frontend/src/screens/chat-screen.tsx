import { Sparkles } from "lucide-react";
import { ChatBubble } from "../components/chat-bubble";
import { ChatInput } from "../components/chat-input";
import { ResultsPanel } from "../components/results-panel";
import { TypingIndicator } from "../components/typing-indicator";
import { SUGGESTION_CARDS } from "../lib/constants";
import type { ChatMessage, ProveedorRecomendado, RecomendacionResponse } from "../types";

type ChatScreenProps = {
  messages: ChatMessage[];
  isPending: boolean;
  handleSend: (text: string) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  onSelectProvider: (provider: ProveedorRecomendado) => void;
  loadingDetail: boolean;
  latestRecommendation: RecomendacionResponse | null;
  onGoHome: () => void;
};

export function ChatScreen({
  messages,
  isPending,
  handleSend,
  messagesEndRef,
  onSelectProvider,
  loadingDetail,
  latestRecommendation,
  onGoHome,
}: ChatScreenProps) {
  const thread = (
    <>
      <div className="chat-messages">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} />
        ))}
        {isPending && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} isPending={isPending} />
    </>
  );

  if (latestRecommendation) {
    return (
      <main className="split-layout">
        <aside className="chat-sidebar">{thread}</aside>
        <ResultsPanel
          recommendation={latestRecommendation}
          onSelectProvider={onSelectProvider}
          loadingDetail={loadingDetail}
          onGoHome={onGoHome}
        />
      </main>
    );
  }

  return (
    <main className="chat-screen">
      {messages.length === 0 ? (
        <div className="chat-welcome">
          <div className="chat-welcome-icon">
            <Sparkles size={28} />
          </div>
          <h2>¿Qué evento estás planeando?</h2>
          <p>
            Cuéntame qué tipo de evento necesitas y te buscaré las mejores opciones
            con disponibilidad en tiempo real.
          </p>
          <div className="suggestion-grid">
            {SUGGESTION_CARDS.map((suggestion) => (
              <button
                className="suggestion-card"
                disabled={isPending}
                key={suggestion.title}
                type="button"
                onClick={() => handleSend(suggestion.query)}
              >
                <span className="suggestion-card-icon">{suggestion.icon}</span>
                <span className="suggestion-card-text">
                  <span className="suggestion-card-title">{suggestion.title}</span>
                  <span className="suggestion-card-desc">{suggestion.description}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      ) : (
        thread
      )}

      {messages.length === 0 && <ChatInput onSend={handleSend} isPending={isPending} />}
    </main>
  );
}
