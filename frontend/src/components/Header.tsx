import { Radar } from "lucide-react";
import type { ReplayStatus } from "../types";

function Chip({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className="flex flex-col rounded-lg border border-ink-600 bg-ink-800 px-3 py-1.5">
      <span className="text-[10px] uppercase tracking-wide text-slate-500">{label}</span>
      <span className={`text-lg font-semibold leading-tight ${accent}`}>{value}</span>
    </div>
  );
}

export function Header({ status, alertCount }: { status: ReplayStatus | null; alertCount: number }) {
  return (
    <header className="flex flex-col gap-4 border-b border-ink-700 bg-ink-900/70 px-5 py-4 backdrop-blur lg:flex-row lg:items-center lg:justify-between">
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-cyan-600/20 ring-1 ring-cyan-500/40">
          <Radar className="h-5 w-5 text-cyan-400" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-white">Crisis Lens</h1>
          <p className="text-xs text-slate-400">AI-assisted signal-to-alert prototype</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 sm:grid-cols-6">
        <Chip label="Pending" value={status?.pending ?? 0} accent="text-slate-200" />
        <Chip label="Released" value={status?.released ?? 0} accent="text-blue-300" />
        <Chip label="Processed" value={status?.processed ?? 0} accent="text-emerald-300" />
        <Chip label="Rejected" value={status?.rejected ?? 0} accent="text-red-300" />
        <Chip label="Total" value={status?.total ?? 0} accent="text-slate-300" />
        <Chip label="Alerts" value={alertCount} accent="text-cyan-300" />
      </div>
    </header>
  );
}
