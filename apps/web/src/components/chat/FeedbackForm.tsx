"use client";

import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/Button";

type FeedbackFormProps = {
  feedbackSent: boolean;
  isSending: boolean;
  onSubmit: (useful: boolean, comment?: string) => Promise<void>;
};

export function FeedbackForm({ feedbackSent, isSending, onSubmit }: FeedbackFormProps) {
  const [comment, setComment] = useState("");
  const shouldReduceMotion = useReducedMotion();

  if (feedbackSent) {
    return (
      <motion.p
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-3 text-center text-xs text-text-tertiary"
      >
        Feedback enviado. ¡Gracias!
      </motion.p>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: "auto" }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.2 }}
      className="mt-4 rounded-xl border border-border-default bg-surface-tertiary/40 p-4"
    >
      <p className="mb-3 flex items-center gap-2 text-sm font-medium text-text-secondary">
        <MessageSquare size={14} />
        ¿Te ha sido útil este diagnóstico?
      </p>

      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          size="sm"
          onClick={async () => {
            await onSubmit(true, comment || undefined);
          }}
          disabled={isSending}
        >
          <ThumbsUp size={14} />
          Sí, útil
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={async () => {
            await onSubmit(false, comment || undefined);
          }}
          disabled={isSending}
        >
          <ThumbsDown size={14} />
          No ayudó
        </Button>
      </div>

      <input
        type="text"
        placeholder="Comentario adicional (opcional)..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        disabled={isSending}
        className="mt-3 w-full rounded-lg border border-border-default bg-surface-secondary/60 px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary transition-colors focus:border-accent-1 focus:outline-none focus:ring-1 focus:ring-accent-1/20"
      />
    </motion.div>
  );
}
