import type { SessionMessageResponse, StartSessionResponse } from "@/types/session";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function startSession(): Promise<StartSessionResponse> {
  const response = await fetch(`${API_BASE}/session/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!response.ok) {
    throw new Error("No se pudo iniciar la sesion");
  }
  return response.json();
}

export async function sendMessage(
  sessionId: string,
  message: string
): Promise<SessionMessageResponse> {
  const response = await fetch(`${API_BASE}/session/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!response.ok) {
    throw new Error("No se pudo enviar el mensaje");
  }
  return response.json();
}

