"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils/cn";

type QuickRepliesProps = {
  replies: string[];
  initialized: boolean;
  isSending: boolean;
  onSelect: (reply: string) => void;
};

export function QuickReplies({ replies, initialized, isSending, onSelect }: QuickRepliesProps) {
  if (replies.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-wrap gap-2"
    >
      {replies.map((reply) => (
        <motion.button
          key={reply}
          type="button"
          onClick={() => onSelect(reply)}
          disabled={!initialized || isSending}
          whileTap={{ scale: 0.95 }}
          className={cn(
            "rounded-full border border-border-default bg-surface-tertiary/50 px-4 py-2",
            "text-xs font-semibold uppercase tracking-wide text-text-secondary",
            "shadow-sm transition-all duration-200",
            "hover:border-accent-1/40 hover:bg-accent-1/10 hover:text-text-primary hover:shadow-glow",
            "active:scale-95",
            "disabled:cursor-not-allowed disabled:opacity-50",
          )}
        >
          {reply}
        </motion.button>
      ))}
    </motion.div>
  );
}
