import { Sparkles, UserRound } from "lucide-react";
import type { ChatMessage } from "../types";

type ChatBubbleProps = {
  message: ChatMessage;
};

/**
 * Renders a single chat message bubble.
 * Cards are no longer embedded — they live in the ResultsPanel.
 */
export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="chat-row chat-row-user">
        <div className="chat-bubble chat-bubble-user">
          <p>{message.content}</p>
        </div>
        <div className="chat-avatar chat-avatar-user">
          <UserRound size={14} />
        </div>
      </div>
    );
  }

  return (
    <div className="chat-row chat-row-assistant">
      <div className="chat-avatar">
        <Sparkles size={14} />
      </div>
      <div className="chat-bubble chat-bubble-assistant">
        <p className="chat-text">{message.content}</p>
      </div>
    </div>
  );
}
