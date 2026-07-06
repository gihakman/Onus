import type { ReactNode } from "react";

export function Container({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mx-auto w-full max-w-6xl px-6 ${className}`}>{children}</div>
  );
}

export function Section({
  id,
  children,
  className = "",
}: {
  id?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section id={id} className={`anchor py-20 md:py-28 ${className}`}>
      {children}
    </section>
  );
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="mb-4 text-xs font-semibold uppercase tracking-[0.16em] text-evidence-ink">
      {children}
    </div>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-lg border border-line bg-paper-raised shadow-card ${className}`}
    >
      {children}
    </div>
  );
}

type Tone = "neutral" | "evidence" | "partial" | "broken" | "active";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-paper-sunken text-ink-muted border-line",
  evidence: "bg-evidence-soft text-evidence-ink border-evidence/20",
  partial: "bg-partial-soft text-partial border-partial/20",
  broken: "bg-broken-soft text-broken border-broken/20",
  active: "bg-evidence-soft text-evidence-ink border-evidence/20",
};

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: Tone;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-sm border px-2 py-0.5 text-xs font-medium ${toneClasses[tone]}`}
    >
      {children}
    </span>
  );
}
