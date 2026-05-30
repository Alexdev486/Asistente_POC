"use client";

import { type KeyboardEvent, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Bike, AlertCircle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";

type ValidationState = "idle" | "validating" | "valid" | "invalid";

type VinInputProps = {
  onSubmit: (vin: string) => Promise<void>;
  disabled?: boolean;
};

export function VinInput({ onSubmit, disabled }: VinInputProps) {
  const [value, setValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validation, setValidation] = useState<ValidationState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [shakeKey, setShakeKey] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || disabled || isSubmitting) return;

    if (trimmed.length < 3) {
      setErrorMessage("Ingresa al menos 3 caracteres");
      setValidation("invalid");
      setShakeKey((k) => k + 1);
      return;
    }

    setValidation("validating");
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await onSubmit(trimmed);
      setValidation("valid");
    } catch {
      setErrorMessage("Error al buscar el bastidor");
      setValidation("invalid");
      setShakeKey((k) => k + 1);
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  }

  const canSubmit = value.trim().length >= 3 && !disabled && !isSubmitting && validation !== "invalid";

  return (
    <div className="w-full max-w-md">
      <motion.div
        key={shakeKey}
        animate={
          validation === "invalid"
            ? { x: [0, -6, 6, -4, 4, 0] }
            : { x: 0 }
        }
        transition={{ duration: 0.35, ease: "easeInOut" }}
        className={cn(
          "group relative flex items-center gap-2 rounded-2xl border-2 p-1.5 transition-all duration-300",
          isFocused && "border-accent-1 bg-surface-secondary shadow-glow",
          !isFocused && validation === "invalid" && "border-red-500 bg-red-950/20",
          !isFocused && validation === "valid" && "border-green-500 bg-green-950/20",
          !isFocused && validation === "idle" && "border-border-default bg-surface-secondary/60",
        )}
      >
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors",
            validation === "valid" ? "bg-green-500/10" : "bg-accent-1/10",
          )}
        >
          {validation === "valid" ? (
            <CheckCircle size={18} className="text-green-400" />
          ) : validation === "invalid" ? (
            <AlertCircle size={18} className="text-red-400" />
          ) : (
            <Bike size={18} className="text-accent-1" />
          )}
        </div>

        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            const next = e.target.value.toUpperCase();
            setValue(next);
            if (validation === "invalid") setValidation("idle");
            if (validation === "valid") setValidation("idle");
          }}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onKeyDown={handleKeyDown}
          disabled={disabled || isSubmitting}
          placeholder="Ingresa el bastidor (VIN)..."
          maxLength={25}
          className={cn(
            "flex-1 bg-transparent px-2 py-2 font-mono text-sm font-medium tracking-wider",
            "placeholder:text-text-tertiary caret-accent-1 focus:outline-none",
            "disabled:cursor-not-allowed disabled:opacity-50",
            validation === "valid" ? "text-green-300" : "text-text-primary",
          )}
          autoComplete="off"
          spellCheck={false}
          aria-label="Bastidor (VIN) de la motocicleta"
          aria-invalid={validation === "invalid"}
          aria-describedby={errorMessage ? "vin-error" : undefined}
        />

        <motion.button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit}
          whileTap={{ scale: 0.95 }}
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all duration-200",
            canSubmit
              ? "bg-gradient-to-r from-accent-1 to-accent-2 text-white shadow-glow hover:shadow-glow-lg"
              : "bg-surface-tertiary text-text-disabled",
          )}
          aria-label="Buscar bastidor"
        >
          {isSubmitting ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
          ) : (
            <ArrowRight size={18} strokeWidth={2.5} />
          )}
        </motion.button>
      </motion.div>

      {/* Inline validation feedback */}
      <AnimatePresence mode="wait">
        {errorMessage && validation === "invalid" && (
          <motion.p
            key="error"
            id="vin-error"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="mt-2 flex items-center gap-1.5 px-4 text-xs text-red-400"
            role="alert"
          >
            <AlertCircle size={12} />
            {errorMessage}
          </motion.p>
        )}
        {validation === "valid" && (
          <motion.p
            key="valid"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            className="mt-2 flex items-center gap-1.5 px-4 text-xs text-green-400"
          >
            <CheckCircle size={12} />
            Buscando modelo...
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  );
}
