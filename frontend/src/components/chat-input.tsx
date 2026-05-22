import { FormEvent, useState } from "react";
import { Loader2, Send } from "lucide-react";

type ChatInputProps = {
  onSend: (text: string) => void;
  isPending: boolean;
  suggestions?: string[];
  showSuggestions?: boolean;
};

/**
 * Fixed-bottom chat input bar with optional quick-suggestion chips.
 */
export function ChatInput({ onSend, isPending, suggestions = [], showSuggestions = false }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clean = value.trim();
    if (!clean || isPending) return;
    onSend(clean);
    setValue("");
  }

  function handleSuggestion(text: string) {
    if (isPending) return;
    onSend(text);
    setValue("");
  }

  return (
    <div className="chat-input-bar">
      <div className="chat-input-inner">
        {showSuggestions && suggestions.length > 0 && (
          <div className="chat-suggestions">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                className="chat-suggestion-chip"
                onClick={() => handleSuggestion(s)}
                disabled={isPending}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Describe tu evento ideal..."
            disabled={isPending}
            autoFocus
          />
          <button type="submit" disabled={isPending || !value.trim()}>
            {isPending ? <Loader2 className="spin" size={20} /> : <Send size={20} />}
          </button>
        </form>
      </div>
    </div>
  );
}
