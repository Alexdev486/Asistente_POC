import { useMemo, useState } from "react";

import { sendMessage, startSession } from "@/lib/api/client";
import type { SessionMessageResponse, SessionState } from "@/types/session";

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [state, setState] = useState<SessionState | null>(null);

  const initialized = useMemo(() => Boolean(sessionId), [sessionId]);

  async function initSession() {
    const result = await startSession();
    setSessionId(result.session_id);
    setMessages([result.message]);
  }

  async function sendUserMessage(text: string): Promise<SessionMessageResponse> {
    if (!sessionId) {
      throw new Error("La sesion aun no esta iniciada");
    }
    const result = await sendMessage(sessionId, text);
    setMessages((prev) => [...prev, text, result.message]);
    setState(result.state);
    return result;
  }

  return {
    sessionId,
    initialized,
    messages,
    state,
    initSession,
    sendUserMessage,
  };
}

