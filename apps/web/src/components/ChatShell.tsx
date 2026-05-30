import type { ReactNode } from "react";

type ChatShellProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
};

export function ChatShell({ title, subtitle, children }: ChatShellProps) {
  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-text-secondary">
            Asistente de Diagnóstico
          </p>
          <h1 className="mt-1 font-display text-3xl font-semibold text-text-primary">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-1.5 text-sm text-text-secondary">{subtitle}</p>
          ) : null}
        </div>
      </header>
      {children}
    </section>
  );
}
