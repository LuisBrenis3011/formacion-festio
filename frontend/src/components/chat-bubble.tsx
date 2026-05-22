import { PartyPopper, UserRound } from "lucide-react";
import { ProviderCard } from "./provider-card";
import type { ChatMessage, ProveedorRecomendado } from "../types";

type ChatBubbleProps = {
  message: ChatMessage;
  onSelectProvider: (provider: ProveedorRecomendado) => void;
  loadingDetail: boolean;
};

/**
 * Renders a single chat message bubble.
 *
 * - User messages: right-aligned, teal background.
 * - Assistant messages: left-aligned with Festio avatar.
 *   If the message has a `recommendation`, it renders the text
 *   followed by provider cards inline — the "hybrid rendering".
 */
export function ChatBubble({ message, onSelectProvider, loadingDetail }: ChatBubbleProps) {
  const isUser = message.role === "user";
  const rec = message.recommendation;
  const principales = rec?.resultados_principales ?? [];
  const otras = rec?.otras_opciones ?? [];
  const hasCards = principales.length > 0 || otras.length > 0;

  if (isUser) {
    return (
      <div className="chat-row chat-row-user">
        <div className="chat-bubble chat-bubble-user">
          <p>{message.content}</p>
        </div>
        <div className="chat-avatar chat-avatar-user">
          <UserRound size={16} />
        </div>
      </div>
    );
  }

  return (
    <div className="chat-row chat-row-assistant">
      <div className="chat-avatar">
        <PartyPopper size={16} />
      </div>
      <div className="chat-bubble chat-bubble-assistant">
        <p className="chat-text">{message.content}</p>

        {hasCards && (
          <div className="chat-cards">
            {principales.length > 0 && (
              <div className="chat-cards-section">
                <span className="chat-cards-label">✨ Mejores coincidencias</span>
                <div className="chat-cards-grid">
                  {principales.map((provider) => (
                    <ProviderCard
                      key={provider.proveedor_id}
                      provider={provider}
                      onSelect={() => onSelectProvider(provider)}
                      disabled={loadingDetail}
                      featured
                    />
                  ))}
                </div>
              </div>
            )}

            {otras.length > 0 && (
              <div className="chat-cards-section">
                <span className="chat-cards-label">Otras alternativas</span>
                <div className="chat-cards-grid">
                  {otras.map((provider) => (
                    <ProviderCard
                      key={provider.proveedor_id}
                      provider={provider}
                      onSelect={() => onSelectProvider(provider)}
                      disabled={loadingDetail}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
