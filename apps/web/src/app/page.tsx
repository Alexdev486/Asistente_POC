"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";

import { ChatShell } from "@/components/ChatShell";
import { useSession } from "@/features/session/useSession";
import type { DiagnosticOutput } from "@/types/session";

export default function HomePage() {
  const { initialized, initSession, sendUserMessage, messages, state, sessionId, isSending, error } =
    useSession();
  const [draft, setDraft] = useState("");
  const [lastDiagnostic, setLastDiagnostic] = useState<DiagnosticOutput | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const shouldReduceMotion = useReducedMotion();

  const canSend = initialized && draft.trim().length > 0 && !isSending;
  const lastAssistant = useMemo(
    () => [...messages].reverse().find((message) => message.role === "assistant")?.text ?? "",
    [messages]
  );
  const quickReplies = useMemo(() => {
    if (!lastAssistant) {
      return [];
    }
    const normalized = lastAssistant.toLowerCase();
    if (normalized.includes("selecciona una opcion")) {
      return ["Sintomas frecuentes", "Consultas frecuentes", "Otros"];
    }
    const optionsMatch = lastAssistant.match(/Opciones:\s*([^)]+)/i);
    if (optionsMatch?.[1]) {
      return optionsMatch[1]
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 4);
    }
    const selectMatch = lastAssistant.match(/Selecciona:\s*([^.]+)/i);
    if (selectMatch?.[1]) {
      return selectMatch[1]
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 4);
    }
    const examplesMatch =
      lastAssistant.match(/Ejemplos?:\s*([^.]+)/i) ?? lastAssistant.match(/como:\s*([^.]+)/i);
    if (examplesMatch?.[1]) {
      return examplesMatch[1]
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 4);
    }
    return [];
  }, [lastAssistant]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: shouldReduceMotion ? "auto" : "smooth" });
  }, [messages, isSending, shouldReduceMotion]);

  async function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !initialized || isSending) {
      return;
    }
    setDraft("");
    const result = await sendUserMessage(text);
    setLastDiagnostic(result.diagnostic_output ?? null);
  }

  return (
    <main className="min-h-screen bg-slate-950 px-4 pb-16 pt-10 text-slate-100">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <ChatShell
        title="Asistente Diagnostico POC"
        subtitle="Demo de flujo guiado (VIN → menu → FAQ/Tree/Otros → feedback)."
      >
        <section className="grid gap-3 rounded-2xl border border-slate-800 bg-slate-900/60 p-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: "Sesion", value: sessionId ?? "No iniciada" },
            { label: "VIN", value: state?.vin ?? "—" },
            { label: "Modelo", value: state?.model ?? "—" },
            { label: "Sintoma", value: state?.current_symptom ?? "—" },
          ].map((item) => (
            <div key={item.label} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
              <span className="text-xs uppercase tracking-[0.2em] text-slate-500">{item.label}</span>
              <div className="mt-2 font-semibold text-slate-100">{item.value}</div>
            </div>
          ))}
        </section>

        <section className="flex flex-col gap-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Conversacion</span>
            {initialized ? (
              <span className="rounded-full border border-slate-800 bg-slate-950/50 px-2 py-1">
                Sesion activa
              </span>
            ) : null}
          </div>
          <div className="flex min-h-[320px] flex-col gap-3 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-950/40 p-4">
            {messages.length === 0 ? (
              <div className="text-sm text-slate-400">
                Inicia una sesion para comenzar el diagnostico.
              </div>
            ) : (
              <AnimatePresence initial={false}>
                {messages.map((message, index) => {
                  const isUser = message.role === "user";
                  const isSystem = message.role === "system";
                  return (
                    <motion.div
                      key={`${message.role}-${index}`}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -12 }}
                      transition={{ duration: shouldReduceMotion ? 0 : 0.2 }}
                      className={`flex ${isUser ? "justify-end" : "justify-start"} ${
                        isSystem ? "justify-center" : ""
                      }`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-sm ${
                          isUser
                            ? "bg-blue-600 text-white"
                            : isSystem
                            ? "bg-slate-800 text-slate-200"
                            : "border border-slate-800 bg-slate-900 text-slate-100"
                        }`}
                      >
                        {message.text}
                      </div>
                    </motion.div>
                  );
                })}
                {isSending ? (
                  <motion.div
                    key="typing"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: shouldReduceMotion ? 0 : 0.2 }}
                    className="flex justify-start"
                  >
                    <div className="flex items-center gap-2 rounded-2xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-slate-300">
                      <span className="h-2 w-2 animate-pulse rounded-full bg-slate-400" />
                      Procesando respuesta...
                    </div>
                  </motion.div>
                ) : null}
              </AnimatePresence>
            )}
            <div ref={bottomRef} />
          </div>

          {lastDiagnostic ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: shouldReduceMotion ? 0 : 0.25 }}
              className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-950/80 via-slate-900/80 to-slate-950/80 p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Diagnostico</p>
                  <h3 className="mt-2 text-lg font-semibold text-slate-50">
                    {lastDiagnostic.primary_hypothesis}
                  </h3>
                </div>
                <div className="rounded-full border border-slate-800 bg-slate-900 px-4 py-2 text-xs text-slate-300">
                  Confianza: {(lastDiagnostic.confidence * 100).toFixed(0)}%
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-300">{lastDiagnostic.short_explanation}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                    Siguiente revision
                  </p>
                  <p className="mt-2 text-sm text-slate-200">{lastDiagnostic.next_check}</p>
                </div>
                <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-500">
                    Alternativas
                  </p>
                  <p className="mt-2 text-sm text-slate-200">
                    {lastDiagnostic.alternatives.length > 0
                      ? lastDiagnostic.alternatives.join(", ")
                      : "Sin alternativas relevantes."}
                  </p>
                </div>
              </div>
            </motion.div>
          ) : null}

          {quickReplies.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {quickReplies.map((reply) => (
                <motion.button
                  key={reply}
                  type="button"
                  onClick={async () => {
                    const result = await sendUserMessage(reply);
                    setLastDiagnostic(result.diagnostic_output ?? null);
                  }}
                  disabled={!initialized || isSending}
                  whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
                  className="rounded-full border border-slate-800 bg-slate-950/60 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 transition hover:border-blue-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {reply}
                </motion.button>
              ))}
            </div>
          ) : null}

          {error ? (
            <div className="rounded-xl border border-red-900 bg-red-950/60 px-4 py-3 text-sm text-red-200">
              {error}
            </div>
          ) : null}

          <div className="flex justify-end">
            <button
              type="button"
              className="rounded-xl border border-slate-800 bg-slate-950/60 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-blue-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
              onClick={async () => {
                await initSession();
                setLastDiagnostic(null);
              }}
              disabled={isSending}
            >
              {initialized ? "Reiniciar sesion" : "Iniciar sesion"}
            </button>
          </div>

          <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Escribe el bastidor o tu consulta..."
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={!initialized || isSending}
              className="flex-1 rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!canSend}
              className="rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Enviar
            </button>
          </form>
        </section>
      </ChatShell>
      </div>
    </main>
  );
}
