"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { ChevronDown, Wrench } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import type { DiagnosticOutput } from "@/types/session";

type DiagnosticPanelProps = {
  diagnostic: DiagnosticOutput;
};

function confidenceColor(value: number): string {
  if (value >= 0.7) return "bg-green-500";
  if (value >= 0.4) return "bg-yellow-500";
  return "bg-red-500";
}

export function DiagnosticPanel({ diagnostic }: DiagnosticPanelProps) {
  const [expanded, setExpanded] = useState(true);
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.25, ease: [0.34, 1.56, 0.64, 1] }}
      className="overflow-hidden rounded-2xl border border-border-default bg-gradient-to-br from-surface-card/90 via-surface-secondary/80 to-surface-card/90"
    >
      {/* Header - always visible */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between gap-3 px-5 py-4 transition-colors hover:bg-surface-tertiary/40"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-1/10">
            <Wrench size={16} className="text-accent-1" />
          </div>
          <div className="text-left">
            <p className="text-xs font-semibold uppercase tracking-[0.15em] text-text-secondary">
              Diagnóstico
            </p>
            <p className="mt-0.5 text-sm font-medium text-text-primary">
              {diagnostic.primary_hypothesis}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Confidence badge */}
          <div className="flex items-center gap-2 rounded-full border border-border-default bg-surface-tertiary/50 px-3 py-1.5">
            <span className="relative h-2 w-14 overflow-hidden rounded-full bg-border-default">
              <motion.span
                className={cn("absolute inset-y-0 left-0 rounded-full", confidenceColor(diagnostic.confidence))}
                initial={{ width: 0 }}
                animate={{ width: `${(diagnostic.confidence * 100).toFixed(0)}%` }}
                transition={{ duration: 0.8, ease: [0.34, 1.56, 0.64, 1] }}
              />
            </span>
            <span className="text-xs font-semibold text-text-secondary">
              {(diagnostic.confidence * 100).toFixed(0)}%
            </span>
          </div>

          <div className="text-text-tertiary transition-transform duration-300" style={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>
            <ChevronDown size={16} />
          </div>
        </div>
      </button>

      {/* Expandable content */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="diagnostic-content"
            initial={shouldReduceMotion ? undefined : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="border-t border-border-default"
          >
            <div className="px-5 pb-5 pt-4">
              <p className="text-sm leading-relaxed text-text-secondary">
                {diagnostic.short_explanation}
              </p>

              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-border-default bg-surface-tertiary/30 p-3.5">
                  <p className="text-xs font-semibold uppercase tracking-[0.15em] text-text-tertiary">
                    Siguiente revisión
                  </p>
                  <p className="mt-1.5 text-sm font-medium text-text-primary">
                    {diagnostic.next_check}
                  </p>
                </div>
                <div className="rounded-xl border border-border-default bg-surface-tertiary/30 p-3.5">
                  <p className="text-xs font-semibold uppercase tracking-[0.15em] text-text-tertiary">
                    Alternativas
                  </p>
                  <p className="mt-1.5 text-sm text-text-secondary">
                    {diagnostic.alternatives.length > 0
                      ? diagnostic.alternatives.join(", ")
                      : "Sin alternativas relevantes."}
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
