"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  Command,
  RefreshCw,
  LogOut,
  PanelLeft,
  Home,
  Search,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

type Action = {
  id: string;
  label: string;
  shortcut?: string;
  icon: React.ReactNode;
  action: () => void;
};

type CommandPaletteProps = {
  actions: Action[];
  enabled?: boolean;
};

export function CommandPalette({ actions, enabled = true }: CommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const filtered = query.trim()
    ? actions.filter((a) => a.label.toLowerCase().includes(query.toLowerCase()))
    : actions;

  // Reset selection when filter changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Keyboard shortcut: Cmd+K or Ctrl+K
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape" && open) {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
    }
  }, [open]);

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      e.preventDefault();
      filtered[selectedIndex].action();
      setOpen(false);
    }
  }

  if (!enabled) return null;

  return (
    <>
      {/* Trigger hint */}
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={cn(
          "fixed bottom-4 left-4 z-50 hidden sm:flex items-center gap-2",
          "rounded-lg border border-border-default bg-surface-secondary/60 px-3 py-1.5",
          "text-xs text-text-tertiary backdrop-blur-xl",
          "transition-all duration-200 hover:border-border-hover hover:text-text-secondary",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-1/40",
        )}
        aria-label="Abrir paleta de comandos"
      >
        <Command size={12} />
        <kbd className="rounded bg-surface-tertiary px-1 font-mono text-[10px]">⌘K</kbd>
      </button>

      {/* Overlay */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[200] flex items-start justify-center bg-black/50 pt-[15vh] backdrop-blur-sm"
            onClick={() => setOpen(false)}
          >
            {/* Palette */}
            <motion.div
              initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: -20, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: -10, scale: 0.97 }}
              transition={{ duration: shouldReduceMotion ? 0 : 0.2, ease: [0.34, 1.56, 0.64, 1] }}
              className="w-full max-w-lg overflow-hidden rounded-2xl border border-border-default bg-surface-secondary shadow-elevated backdrop-blur-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Search input */}
              <div className="flex items-center gap-3 border-b border-border-default px-4 py-3">
                <Search size={16} className="text-text-tertiary" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Buscar acciones..."
                  className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none"
                  autoComplete="off"
                  aria-label="Buscar comando"
                />
                <kbd className="rounded border border-border-default bg-surface-tertiary px-1.5 py-0.5 font-mono text-[10px] text-text-tertiary">
                  Esc
                </kbd>
              </div>

              {/* Actions */}
              <div className="max-h-64 overflow-y-auto p-2">
                {filtered.length === 0 ? (
                  <p className="px-3 py-6 text-center text-sm text-text-tertiary">
                    No se encontraron acciones
                  </p>
                ) : (
                  filtered.map((item, i) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        item.action();
                        setOpen(false);
                      }}
                      onMouseEnter={() => setSelectedIndex(i)}
                      className={cn(
                        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                        i === selectedIndex
                          ? "bg-accent-1/10 text-accent-1"
                          : "text-text-secondary hover:bg-surface-tertiary hover:text-text-primary",
                      )}
                    >
                      <span className="flex h-6 w-6 items-center justify-center">
                        {item.icon}
                      </span>
                      <span className="flex-1">{item.label}</span>
                      {item.shortcut && (
                        <kbd className="rounded border border-border-default bg-surface-tertiary px-1.5 py-0.5 font-mono text-[10px] text-text-tertiary">
                          {item.shortcut}
                        </kbd>
                      )}
                    </button>
                  ))
                )}
              </div>

              {/* Footer hint */}
              <div className="border-t border-border-default px-4 py-2 text-[10px] text-text-tertiary">
                <span className="flex items-center gap-3">
                  <span>↑↓ Navegar</span>
                  <span>↵ Seleccionar</span>
                  <span>Esc Cerrar</span>
                </span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export function useCommandActions(
  onNewSession: () => void,
  onCloseSession: () => void,
  onToggleSidebar: () => void,
  onGoHome: () => void,
  sessionActive: boolean,
): Action[] {
  return [
    { id: "new-session", label: "Nueva sesión", shortcut: "⌘N", icon: <RefreshCw size={14} />, action: onNewSession },
    ...(sessionActive ? [{ id: "close-session", label: "Cerrar sesión", shortcut: "Esc", icon: <LogOut size={14} />, action: onCloseSession }] : []),
    { id: "toggle-sidebar", label: "Alternar panel", shortcut: "⌘B", icon: <PanelLeft size={14} />, action: onToggleSidebar },
    { id: "go-home", label: "Ir al inicio", shortcut: "⌘H", icon: <Home size={14} />, action: onGoHome },
  ];
}
