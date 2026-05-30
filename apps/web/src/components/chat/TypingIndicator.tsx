"use client";

import { motion } from "framer-motion";

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.2 }}
      className="flex justify-start"
    >
      <div className="flex items-center gap-3 rounded-[18px] rounded-bl-[4px] border border-border-default bg-surface-elevated px-4 py-3 text-sm text-text-secondary">
        <span className="flex items-center gap-1.5">
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="h-2 w-2 rounded-full"
              style={{
                background: `linear-gradient(135deg, #3B82F6, ${i === 1 ? "#8B5CF6" : i === 2 ? "#06B6D4" : "#3B82F6"})`,
              }}
              animate={{
                y: [0, -5, 0],
                scale: [1, 1.15, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
                ease: "easeInOut",
              }}
            />
          ))}
        </span>
        <span className="text-xs font-medium tracking-wide opacity-60">
          Pensando...
        </span>
      </div>
    </motion.div>
  );
}
