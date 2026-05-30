import { useEffect, useMemo, useRef, useState } from "react";

import { getSession, sendFeedback, sendMessage, startSession } from "@/lib/api/client";
import type { SessionMessageResponse, SessionState } from "@/types/session";

export type ChatMessage = {
  role: "assistant" | "user" | "system";
  text: string;
  created_at: string;
};

function nowISO(): string {
  return new Date().toISOString();
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function useSession() {
  const [sessionId, _setSessionId] = useState<string | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  function setSessionId(value: string | null) {
    sessionIdRef.current = value;
    _setSessionId(value);
  }

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [state, setState] = useState<SessionState | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedText, setLastFailedText] = useState<string | null>(null);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const storageKey = "asistente.sessionId";

  const initialized = useMemo(() => Boolean(sessionId), [sessionId]);

  useEffect(() => {
    if (typeof window === "undefined" || sessionId) {
      return;
    }
    const stored = window.localStorage.getItem(storageKey);
    if (!stored) {
      return;
    }
    setError(null);
    getSession(stored)
      .then((result) => {
        setSessionId(result.session_id);
        setState(result.state);
        setMessages([{ role: "system", text: "Sesion reanudada.", created_at: nowISO() }]);
      })
      .catch((err) => {
        window.localStorage.removeItem(storageKey);
        setError(err instanceof Error ? err.message : "No se pudo recuperar la sesion.");
      });
  }, [sessionId]);

  async function initSession() {
    setIsSending(true);
    setError(null);
    setLastFailedText(null);
    try {
      const result = await startSession();
      setSessionId(result.session_id);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(storageKey, result.session_id);
      }
      setMessages([{ role: "assistant", text: result.message, created_at: nowISO() }]);
      setState(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar la sesion.");
      throw err;
    } finally {
      setIsSending(false);
    }
  }

  async function sendUserMessage(text: string): Promise<SessionMessageResponse> {
    const sid = sessionIdRef.current;
    if (!sid) {
      throw new Error("La sesion aun no esta iniciada");
    }
    setIsSending(true);
    setError(null);
    setLastFailedText(null);
    try {
      setMessages((prev) => [...prev, { role: "user", text, created_at: nowISO() }]);
      const result = await sendMessage(sid, text);
      setMessages((prev) => [...prev, { role: "assistant", text: result.message, created_at: nowISO() }]);
      setState(result.state);
      return result;
    } catch (err) {
      setLastFailedText(text);
      setError(err instanceof Error ? err.message : "No se pudo enviar el mensaje.");
      throw err;
    } finally {
      setIsSending(false);
    }
  }

  async function retryLastMessage(): Promise<SessionMessageResponse | null> {
    if (!lastFailedText) return null;
    return sendUserMessage(lastFailedText);
  }

  async function submitFeedback(useful: boolean, comment?: string): Promise<void> {
    if (!sessionId) return;
    try {
      await sendFeedback(sessionId, useful, comment);
      setFeedbackSent(true);
      setMessages((prev) => [
        ...prev,
        { role: "system", text: "Feedback guardado. ¡Gracias!", created_at: nowISO() },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo guardar el feedback.");
    }
  }

  async function clearSession() {
    setSessionId(null);
    setMessages([]);
    setState(null);
    setIsSending(false);
    setError(null);
    setLastFailedText(null);
    setFeedbackSent(false);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(storageKey);
    }
  }

  return {
    sessionId,
    initialized,
    messages,
    state,
    isSending,
    error,
    lastFailedText,
    feedbackSent,
    initSession,
    sendUserMessage,
    retryLastMessage,
    submitFeedback,
    clearSession,
    formatTime,
  };
}
