type ChatShellProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

export function ChatShell({ title, subtitle, children }: ChatShellProps) {
  return (
    <section className="flex flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
            Conversational Diagnostics
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-50">{title}</h1>
          {subtitle ? <p className="mt-2 text-sm text-slate-400">{subtitle}</p> : null}
        </div>
      </header>
      {children}
    </section>
  );
}
