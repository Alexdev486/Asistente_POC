"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Copy, Check } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { ChatMessage as ChatMessageType } from "@/features/session/useSession";

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

type ChatMessageProps = {
  message: ChatMessageType;
  index: number;
  isLastAssistant?: boolean;
};

export function ChatMessage({ message, index, isLastAssistant }: ChatMessageProps) {
  const shouldReduceMotion = useReducedMotion();
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isAssistant = !isUser && !isSystem;
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(message.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  }

  // Entrance: user messages slide from right, assistant from left, system fades in
  const originX = isUser ? 20 : isSystem ? 0 : -20;

  return (
    <motion.div
      layout
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, x: originX, scale: 0.97 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: originX * -1, scale: 0.97 }}
      transition={{
        duration: shouldReduceMotion ? 0 : 0.3,
        ease: [0.34, 1.56, 0.64, 1],
        delay: Math.min(index * 0.03, 0.3),
      }}
      className={cn(
        "group flex",
        isUser && "justify-end",
        isSystem && "justify-center",
        isAssistant && "justify-start",
      )}
    >
      <div className={cn("relative max-w-[85%]", isAssistant && "group")}>
        <div
          className={cn(
            "px-4 py-3 text-sm leading-relaxed shadow-sm transition-shadow duration-300",
            isUser && [
              "bg-gradient-to-br from-accent-1 to-blue-500 text-white",
              "rounded-[18px] rounded-br-[4px]",
            ],
            isSystem && [
              "border border-border-default bg-surface-tertiary/60",
              "rounded-full px-5 py-2 text-xs text-center text-text-secondary/75",
            ],
            isAssistant && [
              "border border-border-default border-l-2 rounded-[18px] rounded-bl-[4px]",
              "bg-surface-elevated text-text-primary",
              isLastAssistant
                ? "border-l-accent-1 shadow-glow"
                : "border-l-accent-1/30",
            ],
          )}
        >
          <p className="whitespace-pre-wrap break-words">{message.text}</p>
          <p
            className={cn(
              "mt-1 text-xs",
              isUser ? "text-blue-200" : "text-text-tertiary",
            )}
          >
            {formatTime(message.created_at)}
          </p>
        </div>

        {/* Copy button — only for assistant messages */}
        {isAssistant && (
          <button
            type="button"
            onClick={handleCopy}
            className={cn(
              "absolute -right-8 top-3 flex h-7 w-7 items-center justify-center rounded-md",
              "text-text-tertiary opacity-0 transition-all duration-200",
              "hover:bg-surface-tertiary hover:text-text-secondary",
              "group-hover:opacity-100 focus:opacity-100",
              "focus:outline-none focus-visible:ring-1 focus-visible:ring-accent-1/40",
              copied && "opacity-100 text-green-400",
            )}
            aria-label={copied ? "Copiado" : "Copiar mensaje"}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
        )}
      </div>
    </motion.div>
  );
}
