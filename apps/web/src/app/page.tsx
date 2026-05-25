"use client";

import { useState } from "react";

import { ChatShell } from "@/components/ChatShell";
import { useSession } from "@/features/session/useSession";

export default function HomePage() {
  const { initialized, initSession, sendUserMessage, messages, state, sessionId, isSending, error } =
    useSession();
  const [draft, setDraft] = useState("");

  const canSend = initialized && draft.trim().length > 0 && !isSending;

  async function handleSend(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || !initialized || isSending) {
      return;
    }
    setDraft("");
    await sendUserMessage(text);
  }

  return (
    <main className="app-shell">
      <ChatShell
        title="Asistente Diagnostico POC"
        subtitle="Demo de flujo guiado (VIN → menu → FAQ/Tree/Otros → feedback)."
      >
        <section className="status-panel">
          <div>
            <span className="label">Sesion</span>
            <span className="value">{sessionId ?? "No iniciada"}</span>
          </div>
          <div>
            <span className="label">VIN</span>
            <span className="value">{state?.vin ?? "—"}</span>
          </div>
          <div>
            <span className="label">Modelo</span>
            <span className="value">{state?.model ?? "—"}</span>
          </div>
          <div>
            <span className="label">Sintoma</span>
            <span className="value">{state?.current_symptom ?? "—"}</span>
          </div>
        </section>

        <section className="chat-panel">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="empty-state">
                Inicia una sesion para comenzar el diagnostico.
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
                  <span>{message.text}</span>
                </div>
              ))
            )}
          </div>
          {error ? <div className="error-banner">{error}</div> : null}
          <div className="actions">
            <button
              type="button"
              className="secondary"
              onClick={initSession}
              disabled={isSending}
            >
              {initialized ? "Reiniciar sesion" : "Iniciar sesion"}
            </button>
          </div>
          <form className="composer" onSubmit={handleSend}>
            <input
              type="text"
              placeholder="Escribe el bastidor o tu consulta..."
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              disabled={!initialized || isSending}
            />
            <button type="submit" disabled={!canSend}>
              Enviar
            </button>
          </form>
        </section>
      </ChatShell>
    </main>
  );
}
