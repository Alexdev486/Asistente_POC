import { useMemo, useState } from "react";

import { sendMessage, startSession } from "@/lib/api/client";
import type { SessionMessageResponse, SessionState } from "@/types/session";

export type ChatMessage = {
  role: "assistant" | "user" | "system";
  text: string;
};

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [state, setState] = useState<SessionState | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initialized = useMemo(() => Boolean(sessionId), [sessionId]);

  async function initSession() {
    setIsSending(true);
    setError(null);
    try {
      const result = await startSession();
      setSessionId(result.session_id);
      setMessages([{ role: "assistant", text: result.message }]);
      setState(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar la sesion.");
      throw err;
    } finally {
      setIsSending(false);
    }
  }

  async function sendUserMessage(text: string): Promise<SessionMessageResponse> {
    if (!sessionId) {
      throw new Error("La sesion aun no esta iniciada");
    }
    setIsSending(true);
    setError(null);
    try {
      setMessages((prev) => [...prev, { role: "user", text }]);
      const result = await sendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", text: result.message }]);
      setState(result.state);
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar el mensaje.");
      throw err;
    } finally {
      setIsSending(false);
    }
  }

  return {
    sessionId,
    initialized,
    messages,
    state,
    isSending,
    error,
    initSession,
    sendUserMessage,
  };
}
