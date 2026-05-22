import { PartyPopper } from "lucide-react";

/**
 * Animated "AI is typing..." indicator with three bouncing dots.
 * Shown in the chat while the mutation is pending.
 */
export function TypingIndicator() {
  return (
    <div className="chat-row chat-row-assistant">
      <div className="chat-avatar">
        <PartyPopper size={16} />
      </div>
      <div className="chat-bubble chat-bubble-assistant">
        <div className="typing-dots">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}
