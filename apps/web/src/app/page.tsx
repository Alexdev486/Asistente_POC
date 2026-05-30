"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useState } from "react";
import { DotLottieReact } from "@lottiefiles/dotlottie-react";
import { ChevronDown, RefreshCw, LogOut } from "lucide-react";

import { ChatShell } from "@/components/ChatShell";
import { ChatMessage } from "@/components/chat/ChatMessage";
import { ChatInput } from "@/components/chat/ChatInput";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { QuickReplies } from "@/components/chat/QuickReplies";
import { DiagnosticPanel } from "@/components/chat/DiagnosticPanel";
import { FeedbackForm } from "@/components/chat/FeedbackForm";
import { StatusPanel } from "@/components/layout/StatusPanel";
import { VehicleHero } from "@/components/layout/VehicleHero";
import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/Button";
import { CommandPalette, useCommandActions } from "@/components/shared/CommandPalette";
import { AmbientParticles } from "@/components/shared/AmbientParticles";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { WelcomeScreen } from "@/components/onboarding/WelcomeScreen";
import { AnimatedPage } from "@/components/shared/AnimatedPage";
import { toast } from "@/components/ui/Toast";
import { useSession } from "@/features/session/useSession";
import { useScrollToBottom } from "@/hooks/useScrollToBottom";
import type { DiagnosticOutput } from "@/types/session";

export default function HomePage() {
  const {
    initialized, initSession, sendUserMessage, retryLastMessage,
    messages, state, sessionId, isSending, error,
    feedbackSent, submitFeedback, clearSession,
  } = useSession();

  const [draft, setDraft] = useState("");
  const [lastDiagnostic, setLastDiagnostic] = useState<DiagnosticOutput | null>(null);
  const [lastQuickReplies, setLastQuickReplies] = useState<string[] | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [validatingVin, setValidatingVin] = useState(false);

  const { containerRef, showScrollButton, scrollToBottom } = useScrollToBottom([
    messages, isSending, lastDiagnostic,
  ]);

  const canSend = initialized && draft.trim().length > 0 && !isSending;

  const lastAssistant = useMemo(
    () => [...messages].reverse().find((m) => m.role === "assistant")?.text ?? "",
    [messages],
  );

  const quickReplies = useMemo(() => {
    if (lastQuickReplies && lastQuickReplies.length > 0) return lastQuickReplies;
    if (!lastAssistant) return [];
    const normalized = lastAssistant.toLowerCase();
    if (normalized.includes("selecciona una opcion")) {
      return ["Síntomas frecuentes", "Consultas frecuentes", "Otros"];
    }
    const patterns = [/Opciones:\s*([^.]+)/i, /Selecciona:\s*([^.]+)/i, /Ejemplos?:\s*([^.]+)/i, /como:\s*([^.]+)/i];
    for (const pat of patterns) {
      const match = lastAssistant.match(pat);
      if (match?.[1]) {
        return match[1].split(",").map((s) => s.trim()).filter(Boolean).slice(0, 6);
      }
    }
    return [];
  }, [lastAssistant, lastQuickReplies]);

  // ── Keyboard shortcuts ──────────────────────────────────
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (e.key === "Escape" && initialized) {
        e.preventDefault();
        handleCloseSession();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  });

  // ── Handlers ────────────────────────────────────────────
  async function handleSend() {
    const text = draft.trim();
    if (!text || !initialized || isSending) return;
    try {
      const result = await sendUserMessage(text);
      setLastDiagnostic(result.diagnostic_output ?? null);
      setLastQuickReplies(result.quick_replies ?? null);
      setDraft("");
    } catch { /* handled */ }
  }

  async function handleStartDemo() {
    if (initialized || isSending) return;
    setIsStarting(true);
    try {
      await initSession();
      setLastDiagnostic(null);
      setLastQuickReplies(null);
    } finally {
      setIsStarting(false);
    }
  }

  async function handleVinSubmit(vin: string) {
    if (initialized || isSending) return;
    setIsStarting(true);
    setValidatingVin(true);
    try {
      await initSession();
      try {
        await sendUserMessage(vin);
      } catch {
        // VIN inválido — volver al WelcomeScreen
        clearSession();
        setLastDiagnostic(null);
        setLastQuickReplies(null);
        setValidatingVin(false);
        throw new Error("VIN no reconocido");
      }
      setValidatingVin(false);
    } finally {
      setIsStarting(false);
    }
  }

  function handleCloseSession() {
    clearSession();
    setLastDiagnostic(null);
    setLastQuickReplies(null);
    toast("success", "Sesión cerrada.");
  }

  const handleQuickReply = useCallback(async (reply: string) => {
    try {
      const result = await sendUserMessage(reply);
      setLastDiagnostic(result.diagnostic_output ?? null);
      setLastQuickReplies(result.quick_replies ?? null);
    } catch { /* handled */ }
  }, [sendUserMessage]);

  const showWelcome = (!initialized && messages.length === 0) || validatingVin;

  // ── Single return with AnimatePresence ─────────────────────
  return (
    <AnimatePresence mode="wait">
      {showWelcome ? (
        <AnimatedPage key="welcome" id="welcome" className="min-h-screen">
          <WelcomeScreen
            onStart={handleStartDemo}
            onVinSubmit={handleVinSubmit}
            isStarting={isStarting}
          />
        </AnimatedPage>
      ) : (
        <AnimatedPage key="chat" id="chat" className="min-h-screen bg-chat-gradient">
          <ChatView
            initialized={initialized}
            sessionId={sessionId}
            state={state}
            messages={messages}
            isSending={isSending}
            error={error}
            feedbackSent={feedbackSent}
            lastDiagnostic={lastDiagnostic}
            quickReplies={quickReplies}
            canSend={canSend}
            draft={draft}
            setDraft={setDraft}
            containerRef={containerRef}
            showScrollButton={showScrollButton}
            scrollToBottom={scrollToBottom}
            handleSend={handleSend}
            handleCloseSession={handleCloseSession}
            handleQuickReply={handleQuickReply}
            initSession={initSession}
            retryLastMessage={retryLastMessage}
            submitFeedback={submitFeedback}
            setLastDiagnostic={setLastDiagnostic}
            setLastQuickReplies={setLastQuickReplies}
          />
        </AnimatedPage>
      )}
    </AnimatePresence>
  );
}

// ── Extracted Chat View ──────────────────────────────────────
type ChatViewProps = {
  initialized: boolean;
  sessionId: string | null;
  state: import("@/types/session").SessionState | null;
  messages: import("@/features/session/useSession").ChatMessage[];
  isSending: boolean;
  error: string | null;
  feedbackSent: boolean;
  lastDiagnostic: DiagnosticOutput | null;
  quickReplies: string[];
  canSend: boolean;
  draft: string;
  setDraft: (v: string) => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
  showScrollButton: boolean;
  scrollToBottom: (behavior?: ScrollBehavior) => void;
  handleSend: () => Promise<void>;
  handleCloseSession: () => void;
  handleQuickReply: (reply: string) => Promise<void>;
  initSession: () => Promise<void>;
  retryLastMessage: () => Promise<import("@/types/session").SessionMessageResponse | null>;
  submitFeedback: (useful: boolean, comment?: string) => Promise<void>;
  setLastDiagnostic: (d: DiagnosticOutput | null) => void;
  setLastQuickReplies: (r: string[] | null) => void;
};

function ChatView({
  initialized, sessionId, state, messages, isSending, error, feedbackSent,
  lastDiagnostic, quickReplies, canSend, draft, setDraft,
  containerRef, showScrollButton, scrollToBottom,
  handleSend, handleCloseSession, handleQuickReply,
  initSession, retryLastMessage, submitFeedback,
  setLastDiagnostic, setLastQuickReplies,
}: ChatViewProps) {
  const commandActions = useCommandActions(
    async () => { await initSession(); setLastDiagnostic(null); setLastQuickReplies(null); },
    handleCloseSession,
    () => { /* sidebar manages own state */ },
    () => handleCloseSession(),
    !!sessionId,
  );

  // Find the index of the last assistant message for glow effect
  const lastAssistantIndex = (() => {
    let idx = -1;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "assistant") {
        idx = i;
        break;
      }
    }
    return idx;
  })();

  return (
    <main className="relative min-h-screen bg-chat-gradient px-4 pb-28 pl-4 pt-4 text-text-primary sm:pl-16 sm:pb-16">
      {/* Ambient particles */}
      <AmbientParticles />

      {/* Command palette */}
      <CommandPalette actions={commandActions} enabled={!!sessionId} />

      <Sidebar
        sessionId={sessionId}
        state={state}
        onNewSession={async () => {
          await initSession();
          setLastDiagnostic(null);
          setLastQuickReplies(null);
        }}
        onCloseSession={handleCloseSession}
        disabled={isSending}
      />

      <ChatShell title="Diagnóstico Inteligente" subtitle="Asistente conversacional para diagnóstico técnico de motocicletas.">
        {/* Vehicle photo hero — grande, encima del chat */}
        {state?.photo_url && (
          <VehicleHero photoUrl={state.photo_url} modelName={state.model} />
        )}

        <StatusPanel sessionId={sessionId} state={state} />

        <ErrorBoundary>
        <section className="flex flex-col gap-4 rounded-2xl border border-border-default bg-surface-elevated/50 p-4">
          {/* Header */}
          <div className="flex items-center justify-between text-xs text-text-secondary">
            <div className="flex items-center gap-3">
              {/* Robot animation — visible solo cuando la IA está pensando */}
              {isSending && (
                <div className="h-8 w-8">
                  <DotLottieReact
                    src="/design/robotanimationchat.lottie"
                    loop
                    autoplay
                    style={{ width: "100%", height: "100%" }}
                  />
                </div>
              )}
              <span className="font-semibold uppercase tracking-[0.15em]">
                {isSending ? "La IA está analizando..." : "Conversación"}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {initialized ? (
                <>
                  <span className="rounded-full border border-border-default bg-surface-tertiary/50 px-2.5 py-1 text-xs font-medium text-text-secondary">
                    Sesión activa
                  </span>
                  <Button variant="danger" size="sm" onClick={handleCloseSession} disabled={isSending}>
                    <LogOut size={12} />
                    Cerrar
                  </Button>
                </>
              ) : null}
            </div>
          </div>

          {/* Messages */}
          <div className="relative">
          <div
            ref={containerRef}
            className="flex max-h-[60vh] min-h-[280px] flex-col gap-3 overflow-y-auto rounded-2xl border border-border-default bg-surface-secondary/60 p-4 scrollbar-thin"
          >
              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <ChatMessage key={`${msg.role}-${i}-${msg.created_at}`} message={msg} index={i} isLastAssistant={i === lastAssistantIndex} />
                ))}
                {isSending && <TypingIndicator key="typing" />}
              </AnimatePresence>
            </div>
            {showScrollButton && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => scrollToBottom("smooth")}
                className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-full border border-border-default bg-surface-secondary/90 text-text-secondary shadow-elevated backdrop-blur-xl transition-all duration-200 hover:border-accent-1/30 hover:text-accent-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-1/40"
                aria-label="Ir al final"
              >
                <ChevronDown size={16} />
              </motion.button>
            )}
          </div>

          {/* Diagnostic Panel */}
          {lastDiagnostic && <DiagnosticPanel diagnostic={lastDiagnostic} />}

          {/* Feedback */}
          {lastDiagnostic && (
            <FeedbackForm feedbackSent={feedbackSent} isSending={isSending} onSubmit={submitFeedback} />
          )}

          {/* Quick replies */}
          <QuickReplies replies={quickReplies} initialized={initialized} isSending={isSending} onSelect={handleQuickReply} />

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-xl border border-red-900 bg-red-950/60 px-4 py-3 text-sm text-red-200"
            >
              <p>{error}</p>
              <Button variant="danger" size="sm" onClick={async () => {
                try {
                  const result = await retryLastMessage();
                  if (result) {
                    setLastDiagnostic(result.diagnostic_output ?? null);
                    setLastQuickReplies(result.quick_replies ?? null);
                  }
                } catch { /* handled */ }
              }} disabled={isSending} className="mt-2">
                Reintentar
              </Button>
            </motion.div>
          )}

          {/* Actions */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs text-text-tertiary">
              Presiona <kbd className="rounded border border-border-default bg-surface-tertiary px-1.5 py-0.5 font-mono text-[10px]">Esc</kbd> para cerrar sesión
            </span>
            <Button variant="secondary" size="sm" onClick={async () => {
              await initSession();
              setLastDiagnostic(null);
              setLastQuickReplies(null);
            }} disabled={isSending}>
              <RefreshCw size={14} />
              {initialized ? "Reiniciar" : "Iniciar sesión"}
            </Button>
          </div>

          {/* Input */}
          <ChatInput
            draft={draft}
            setDraft={setDraft}
            canSend={canSend}
            isSending={isSending}
            initialized={initialized}
            onSubmit={handleSend}
            placeholder={initialized ? "Escribe tu mensaje..." : "Inicia una sesión para escribir..."}
          />

          <p className="text-center text-[10px] text-text-disabled sm:hidden">
            Escritorio: presiona Esc para cerrar sesión
          </p>
        </section>
        </ErrorBoundary>
      </ChatShell>
    </main>
  );
}
