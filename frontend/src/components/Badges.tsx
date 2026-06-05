import type { ReactNode } from "react";

function Pill({ children, className }: { children: ReactNode; className: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${className}`}
    >
      {children}
    </span>
  );
}

const RISK_STYLES: Record<string, string> = {
  critical: "bg-red-500/15 text-red-300 ring-red-500/30",
  high: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  medium: "bg-yellow-500/10 text-yellow-200 ring-yellow-500/25",
  low: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
};

export function RiskBadge({ level }: { level: string | null | undefined }) {
  const key = (level ?? "unknown").toLowerCase();
  return <Pill className={RISK_STYLES[key] ?? "bg-slate-500/15 text-slate-300 ring-slate-500/30"}>{level ?? "unknown"}</Pill>;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-slate-500/15 text-slate-300 ring-slate-500/30",
  released: "bg-blue-500/15 text-blue-300 ring-blue-500/30",
  processed: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  rejected: "bg-red-500/15 text-red-300 ring-red-500/30",
  new: "bg-cyan-500/15 text-cyan-300 ring-cyan-500/30",
  acknowledged: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  dismissed: "bg-slate-500/15 text-slate-400 ring-slate-500/30",
};

export function StatusBadge({ status }: { status: string }) {
  return <Pill className={STATUS_STYLES[status.toLowerCase()] ?? "bg-slate-500/15 text-slate-300 ring-slate-500/30"}>{status}</Pill>;
}

export function SourceBadge({ sourceType }: { sourceType: string | null }) {
  if (sourceType === "eonet_event")
    return <Pill className="bg-violet-500/15 text-violet-300 ring-violet-500/30">NASA EONET Event</Pill>;
  if (sourceType === "wikinews_dump")
    return <Pill className="bg-sky-500/15 text-sky-300 ring-sky-500/30">Wikinews Article</Pill>;
  return <Pill className="bg-slate-500/15 text-slate-300 ring-slate-500/30">{sourceType ?? "signal"}</Pill>;
}

export function Tag({ children }: { children: ReactNode }) {
  return <Pill className="bg-ink-500/40 text-slate-300 ring-ink-500">{children}</Pill>;
}
