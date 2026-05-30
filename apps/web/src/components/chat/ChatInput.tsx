"use client";

import { type KeyboardEvent, useRef } from "react";
import TextareaAutosize from "react-textarea-autosize";
import { ArrowUp } from "lucide-react";
import { cn } from "@/lib/utils/cn";

type ChatInputProps = {
  draft: string;
  setDraft: (value: string) => void;
  canSend: boolean;
  isSending: boolean;
  initialized: boolean;
  onSubmit: () => void;
  placeholder?: string;
};

export function ChatInput({
  draft,
  setDraft,
  canSend,
  isSending,
  initialized,
  onSubmit,
  placeholder = "Escribe tu mensaje...",
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) onSubmit();
    }
  }

  return (
    <div className="relative flex items-end gap-2">
      <div className="relative flex-1">
        <TextareaAutosize
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!initialized || isSending}
          maxRows={4}
          placeholder={placeholder}
          className={cn(
            "w-full resize-none rounded-2xl border border-border-default bg-surface-secondary/80 px-4 py-3 pr-12 text-sm",
            "text-text-primary placeholder:text-text-tertiary",
            "transition-all duration-200",
            "focus:border-accent-1 focus:outline-none focus:ring-2 focus:ring-accent-1/20",
            "backdrop-blur-xl",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        />
      </div>

      <button
        type="button"
        onClick={onSubmit}
        disabled={!canSend}
        className={cn(
          "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl",
          "bg-gradient-to-r from-accent-1 to-accent-2 text-white",
          "shadow-glow transition-all duration-200",
          "hover:scale-105 hover:shadow-glow-lg",
          "active:scale-95",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-1/40",
          "disabled:cursor-not-allowed disabled:opacity-30 disabled:shadow-none disabled:hover:scale-100",
        )}
        aria-label="Enviar mensaje"
      >
        <ArrowUp size={18} strokeWidth={2.5} />
      </button>
    </div>
  );
}
