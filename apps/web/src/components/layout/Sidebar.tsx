"use client";

import { useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  PanelLeftOpen,
  PanelLeftClose,
  Bike,
  RefreshCw,
  LogOut,
  MessageSquare,
  Wrench,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils/cn";
import type { SessionState } from "@/types/session";

type SidebarProps = {
  sessionId: string | null;
  state: SessionState | null;
  onNewSession: () => void;
  onCloseSession: () => void;
  disabled?: boolean;
};

export function Sidebar({ sessionId, state, onNewSession, onCloseSession, disabled }: SidebarProps) {
  const [open, setOpen] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  const toggle = () => setOpen((prev) => !prev);
  const close = () => setOpen(false);

  const panelContent = (
    <>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-1/10">
            <Bike size={16} className="text-accent-1" />
          </div>
          <span className="text-sm font-semibold text-text-primary">Asistente</span>
        </div>
        <button
          type="button"
          onClick={close}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-text-tertiary transition-colors hover:bg-surface-tertiary hover:text-text-primary"
        >
          <PanelLeftClose size={16} />
        </button>
      </div>

      {/* Session info */}
      <div className="flex flex-col gap-3">
        <p className="text-xs font-semibold uppercase tracking-[0.15em] text-text-tertiary">
          Sesión
        </p>
        <div className="space-y-2">
          <SidebarRow icon={<Activity size={14} />} label="Estado" value={sessionId ? "Activa" : "Inactiva"} />
          {sessionId && (
            <SidebarRow icon={<MessageSquare size={14} />} label="ID" value={sessionId.slice(0, 8) + "…"} mono />
          )}
          {state?.vin && <SidebarRow icon={<Wrench size={14} />} label="VIN" value={state.vin} mono />}
          {state?.model && <SidebarRow icon={<Bike size={14} />} label="Modelo" value={state.model} />}
        </div>
      </div>

      {/* Vehicle photo */}
      {state?.photo_url && (
        <div className="overflow-hidden rounded-xl border border-border-default">
          <img
            src={`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"}/${state.photo_url.replace("/api/v1/", "")}`}
            alt={state.model ?? "Vehículo"}
            className="h-32 w-full object-cover"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
          />
        </div>
      )}

      {/* Actions */}
      <div className="mt-auto flex flex-col gap-2">
        <p className="text-xs font-semibold uppercase tracking-[0.15em] text-text-tertiary">Acciones</p>
        <Button variant="secondary" size="sm" onClick={() => { onNewSession(); close(); }} disabled={disabled}>
          <RefreshCw size={14} />
          Nueva sesión
        </Button>
        {sessionId ? (
          <Button variant="danger" size="sm" onClick={() => { onCloseSession(); close(); }} disabled={disabled}>
            <LogOut size={14} />
            Cerrar sesión
          </Button>
        ) : null}
      </div>
    </>
  );

  const duration = shouldReduceMotion ? 0 : 0.3;
  const easing: [number, number, number, number] = [0.22, 1, 0.36, 1];

  return (
    <>
      {/* Toggle button — hidden on mobile (use bottom-nav instead) */}
      <button
        type="button"
        onClick={toggle}
        className={cn(
          "fixed left-4 top-4 z-50 hidden sm:flex h-10 w-10 items-center justify-center rounded-xl",
          "border border-border-default bg-surface-secondary/80 text-text-secondary",
          "backdrop-blur-xl transition-all duration-200",
          "hover:border-border-hover hover:text-text-primary",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-1/40",
        )}
        aria-label={open ? "Cerrar panel" : "Abrir panel"}
      >
        {open ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
      </button>

      {/* Mobile bottom‑sheet trigger */}
      <button
        type="button"
        onClick={toggle}
        className={cn(
          "fixed bottom-6 left-1/2 z-50 -translate-x-1/2 sm:hidden",
          "flex items-center gap-2 rounded-full border border-border-default bg-surface-secondary/90 px-5 py-2.5",
          "text-xs font-medium text-text-secondary shadow-elevated backdrop-blur-xl",
          "transition-all duration-200 active:scale-95",
          "hover:border-border-hover hover:text-text-primary",
        )}
        aria-label="Abrir panel"
      >
        <Bike size={14} />
        Panel
      </button>

      {/* Overlay — full screen on mobile, behind sidebar on desktop */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
            onClick={close}
          />
        )}
      </AnimatePresence>

      {/* Panel: left sidebar on desktop, bottom sheet on mobile */}
      <AnimatePresence>
        {open && (
          <>
            {/* Desktop sidebar */}
            <motion.aside
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ duration, ease: easing }}
              className={cn(
                "fixed left-0 top-0 z-50 hidden sm:flex h-full w-72 flex-col gap-6",
                "border-r border-border-default bg-surface-secondary p-6",
                "shadow-elevated backdrop-blur-xl",
              )}
            >
              {panelContent}
            </motion.aside>

            {/* Mobile bottom sheet */}
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ duration, ease: easing }}
              className={cn(
                "fixed inset-x-0 bottom-0 z-50 flex flex-col gap-6 sm:hidden",
                "rounded-t-2xl border border-border-default bg-surface-secondary p-6 pb-10",
                "shadow-elevated backdrop-blur-xl",
                "max-h-[80vh] overflow-y-auto",
              )}
            >
              {/* Drag handle */}
              <div className="mx-auto h-1 w-10 shrink-0 rounded-full bg-border-default" />
              {panelContent}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

type SidebarRowProps = {
  icon: React.ReactNode;
  label: string;
  value: string;
  mono?: boolean;
};

function SidebarRow({ icon, label, value, mono }: SidebarRowProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-surface-primary/40 px-3 py-2">
      <span className="text-text-tertiary">{icon}</span>
      <div className="flex flex-1 items-baseline justify-between gap-2">
        <span className="text-xs text-text-tertiary">{label}</span>
        <span className={cn("text-xs font-medium text-text-primary", mono && "font-mono tracking-wider")}>
          {value}
        </span>
      </div>
    </div>
  );
}
