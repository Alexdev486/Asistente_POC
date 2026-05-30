"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils/cn";

export type ToastType = "success" | "error" | "info" | "warning";

type Toast = {
  id: string;
  type: ToastType;
  message: string;
};

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const styles: Record<ToastType, string> = {
  success: "border-green-700 bg-green-950/60 text-green-200",
  error: "border-red-700 bg-red-950/60 text-red-200",
  info: "border-accent-1 bg-accent-1/10 text-blue-200",
  warning: "border-yellow-700 bg-yellow-950/60 text-yellow-200",
};

const iconStyles: Record<ToastType, string> = {
  success: "text-green-400",
  error: "text-red-400",
  info: "text-accent-1",
  warning: "text-yellow-400",
};

// Global toast state
let addToastFn: ((type: ToastType, message: string) => void) | null = null;

export function toast(type: ToastType, message: string) {
  if (addToastFn) addToastFn(type, message);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    addToastFn = (type: ToastType, message: string) => {
      const id = Math.random().toString(36).slice(2);
      setToasts((prev) => [...prev, { id, type, message }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    };
    return () => { addToastFn = null; };
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      <AnimatePresence mode="popLayout">
        {toasts.map((t) => {
          const Icon = icons[t.type];
          return (
            <motion.div
              key={t.id}
              layout
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95, transition: { duration: 0.15 } }}
              transition={{ duration: shouldReduceMotion ? 0 : 0.25, ease: [0.34, 1.56, 0.64, 1] }}
              className={cn(
                "flex items-center gap-3 rounded-xl border px-4 py-3 text-sm shadow-elevated backdrop-blur-xl",
                styles[t.type],
              )}
            >
              <Icon size={16} className={cn("shrink-0", iconStyles[t.type])} />
              <span className="flex-1">{t.message}</span>
              <button
                type="button"
                onClick={() => removeToast(t.id)}
                className="shrink-0 opacity-60 transition-opacity hover:opacity-100"
              >
                <X size={14} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
