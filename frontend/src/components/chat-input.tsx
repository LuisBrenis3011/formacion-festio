import { FormEvent, useState } from "react";
import { Loader2, Send } from "lucide-react";

type ChatInputProps = {
  onSend: (text: string) => void;
  isPending: boolean;
  placeholder?: string;
};

/**
 * Fixed-bottom chat input bar — clean and focused.
 * Suggestions are now rendered separately in the welcome screen.
 */
export function ChatInput({ onSend, isPending, placeholder = "Describe tu evento ideal..." }: ChatInputProps) {
  const [value, setValue] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const clean = value.trim();
    if (!clean || isPending) return;
    onSend(clean);
    setValue("");
  }

  return (
    <div className="chat-input-bar">
      <div className="chat-input-inner">
        <form className="chat-input-form" onSubmit={handleSubmit}>
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={placeholder}
            disabled={isPending}
            autoFocus
          />
          <button type="submit" disabled={isPending || !value.trim()}>
            {isPending ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
          </button>
        </form>
      </div>
    </div>
  );
}
