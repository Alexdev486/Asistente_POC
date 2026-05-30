import type { MessagesListResponse, SessionDetailResponse, SessionMessageResponse, StartSessionResponse } from "@/types/session";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT_MS = 25_000;

async function fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export async function startSession(): Promise<StartSessionResponse> {
  const response = await fetchWithTimeout(`${API_BASE}/session/start`, {
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
  const response = await fetchWithTimeout(`${API_BASE}/session/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!response.ok) {
    throw new Error("No se pudo enviar el mensaje");
  }
  return response.json();
}

export async function getSession(sessionId: string): Promise<SessionDetailResponse> {
  const response = await fetchWithTimeout(`${API_BASE}/session/${sessionId}`);
  if (!response.ok) {
    throw new Error("No se pudo recuperar la sesion");
  }
  return response.json();
}

export async function getMessages(sessionId: string): Promise<MessagesListResponse> {
  const response = await fetchWithTimeout(`${API_BASE}/session/${sessionId}/messages`);
  if (!response.ok) {
    throw new Error("No se pudieron recuperar los mensajes");
  }
  return response.json();
}

export async function sendFeedback(
  sessionId: string,
  useful: boolean,
  comment?: string,
): Promise<{ session_id: string; saved: boolean; message: string }> {
  const body: Record<string, unknown> = { useful };
  if (comment !== undefined) {
    body.comment = comment;
  }
  const response = await fetchWithTimeout(`${API_BASE}/session/${sessionId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error("No se pudo guardar el feedback");
  }
  return response.json();
}
