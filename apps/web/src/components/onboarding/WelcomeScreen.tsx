"use client";

import { motion, useReducedMotion } from "framer-motion";
import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import { Sparkles } from "lucide-react";
import { VinInput } from "@/components/onboarding/VinInput";
import { Button } from "@/components/ui/Button";
import { AmbientParticles } from "@/components/shared/AmbientParticles";

type WelcomeScreenProps = {
  onStart: () => Promise<void>;
  onVinSubmit: (vin: string) => Promise<void>;
  isStarting: boolean;
};

export function WelcomeScreen({ onStart, onVinSubmit, isStarting }: WelcomeScreenProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-chat-gradient px-4">
      {/* Ambient particles */}
      <AmbientParticles />

      {/* Animated background gradient */}
      {!shouldReduceMotion && (
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="animate-drift absolute -inset-[50%] bg-[radial-gradient(ellipse_40%_50%_at_50%_50%,rgba(59,130,246,0.08),transparent_70%)]" />
        </div>
      )}

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="flex w-full max-w-md flex-col items-center gap-10"
      >
        {/* Robot animation — grande y centrada */}
        <motion.div
          initial={{ scale: shouldReduceMotion ? 1 : 0.85, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.34, 1.56, 0.64, 1] }}
        >
          <div className="flex h-64 w-64 items-center justify-center sm:h-72 sm:w-72">
            <DotLottieReact
              src="/design/robot-animation.lottie"
              loop
              autoplay
              style={{ width: "100%", height: "100%" }}
            />
          </div>
        </motion.div>

        {/* Text */}
        <motion.div
          initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-center"
        >
          <h1 className="font-display text-3xl font-semibold text-text-primary sm:text-4xl">
            Diagnóstico Inteligente
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-text-secondary">
            Asistente conversacional para diagnóstico técnico de motocicletas.
          </p>
        </motion.div>

        {/* VIN Input */}
        <motion.div
          initial={{ opacity: 0, y: shouldReduceMotion ? 0 : 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.35 }}
          className="w-full"
        >
          <VinInput onSubmit={onVinSubmit} disabled={isStarting} />
        </motion.div>

        {/* Divider + Demo */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="flex w-full flex-col items-center gap-5"
        >
          <div className="flex w-full items-center gap-4">
            <div className="h-px flex-1 bg-border-default" />
            <span className="text-xs font-medium uppercase tracking-wider text-text-tertiary">
              O continúa como invitado
            </span>
            <div className="h-px flex-1 bg-border-default" />
          </div>

          <Button
            variant="gradient"
            size="lg"
            onClick={onStart}
            disabled={isStarting}
            loading={isStarting}
          >
            <Sparkles size={16} />
            Iniciar demo
          </Button>
        </motion.div>

        {/* Footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="mt-4 text-xs text-text-tertiary"
        >
          Demo POC — Asistente de Diagnóstico Técnico
        </motion.p>
      </motion.div>
    </main>
  );
}
