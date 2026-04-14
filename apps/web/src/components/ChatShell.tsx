type ChatShellProps = {
  title: string;
  subtitle?: string;
};

export function ChatShell({ title, subtitle }: ChatShellProps) {
  return (
    <section>
      <h2>{title}</h2>
      {subtitle ? <p>{subtitle}</p> : null}
    </section>
  );
}

