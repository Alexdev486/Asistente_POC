type ChatShellProps = {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
};

export function ChatShell({ title, subtitle, children }: ChatShellProps) {
  return (
    <section className="chat-shell">
      <header className="chat-header">
        <div>
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
      </header>
      {children}
    </section>
  );
}
