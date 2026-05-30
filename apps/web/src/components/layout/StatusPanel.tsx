"use client";

import type { SessionState } from "@/types/session";
import { cn } from "@/lib/utils/cn";

type StatusPanelProps = {
  sessionId: string | null;
  state: SessionState | null;
};

type StatusItem = {
  label: string;
  value: string;
  highlight?: boolean;
};

export function StatusPanel({ sessionId, state }: StatusPanelProps) {
  const items: StatusItem[] = [
    { label: "Sesión", value: sessionId ?? "No iniciada" },
    { label: "VIN", value: state?.vin ?? "—" },
    { label: "Modelo", value: state?.model ?? "—" },
    ...(state?.current_symptom ? [{ label: "Síntoma", value: state.current_symptom }] : []),
    ...(state?.current_node ? [{ label: "Nodo", value: state.current_node }] : []),
  ];

  if (items.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-4 rounded-2xl border border-border-default bg-surface-secondary/60 p-4">
      <div className="grid flex-1 gap-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-border-default bg-surface-primary/40 p-3"
          >
            <span className="text-xs font-semibold uppercase tracking-[0.15em] text-text-tertiary">
              {item.label}
            </span>
            <div
              className={cn(
                "mt-1.5 font-semibold",
                item.highlight ? "text-accent-1" : "text-text-primary",
              )}
            >
              {item.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
