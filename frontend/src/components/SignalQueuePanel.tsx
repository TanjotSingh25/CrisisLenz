import { useState } from "react";
import { ListTree, Play, RefreshCw, RotateCcw, SkipForward } from "lucide-react";
import type { ReplaySignal } from "../types";
import { Button, Card, EmptyState } from "./ui";
import { SourceBadge } from "./Badges";

const SOURCES = [
  { key: "all", label: "All" },
  { key: "wikinews_dump", label: "Wikinews" },
  { key: "eonet_event", label: "EONET" },
];

export function SignalQueuePanel({
  pending,
  source,
  onSourceChange,
  onReleaseNext,
  onReleaseSpecific,
  onReset,
  onRefresh,
  busy,
}: {
  pending: ReplaySignal[];
  source: string;
  onSourceChange: (s: string) => void;
  onReleaseNext: () => void;
  onReleaseSpecific: (signal: ReplaySignal) => void;
  onReset: () => void;
  onRefresh: () => void;
  busy: boolean;
}) {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <Card title="Signal Intake" icon={<ListTree className="h-4 w-4 text-cyan-400" />}>
      <div className="space-y-3">
        {/* Source filter */}
        <div className="flex gap-1 rounded-lg bg-ink-900/60 p-1">
          {SOURCES.map((s) => (
            <button
              key={s.key}
              onClick={() => onSourceChange(s.key)}
              className={`flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors ${
                source === s.key ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Controls */}
        <div className="grid grid-cols-2 gap-2">
          <Button variant="primary" onClick={onReleaseNext} loading={busy} icon={<SkipForward className="h-4 w-4" />}>
            Release Next
          </Button>
          <Button
            variant="subtle"
            disabled={selectedId === null}
            onClick={() => {
              const sig = pending.find((p) => p.id === selectedId);
              if (sig) onReleaseSpecific(sig);
            }}
            icon={<Play className="h-4 w-4" />}
          >
            Release Selected
          </Button>
          <Button variant="ghost" onClick={onRefresh} icon={<RefreshCw className="h-4 w-4" />}>
            Refresh
          </Button>
          <Button variant="ghost" onClick={onReset} icon={<RotateCcw className="h-4 w-4" />}>
            Reset Replay
          </Button>
        </div>

        {/* Pending list */}
        <div className="text-[11px] uppercase tracking-wide text-slate-500">
          Pending Signals ({pending.length})
        </div>
        <div className="max-h-[420px] space-y-1.5 overflow-y-auto pr-1">
          {pending.length === 0 && <EmptyState>No pending signals. Reset the replay to refill the queue.</EmptyState>}
          {pending.map((sig) => (
            <button
              key={sig.id}
              onClick={() => setSelectedId(sig.id)}
              className={`w-full rounded-lg border px-3 py-2 text-left transition-colors ${
                selectedId === sig.id
                  ? "border-cyan-500/60 bg-cyan-500/5"
                  : "border-ink-600 bg-ink-800 hover:border-ink-500"
              }`}
            >
              <div className="mb-1 flex items-center justify-between gap-2">
                <SourceBadge sourceType={sig.source_type} />
                {sig.event_category && <span className="text-[10px] text-slate-500">{sig.event_category}</span>}
              </div>
              <div className="line-clamp-2 text-xs text-slate-200">{sig.title}</div>
              <div className="mt-1 flex items-center gap-2 text-[10px] text-slate-500">
                {sig.category_hint && <span>{sig.category_hint}</span>}
                {sig.filter_score != null && <span>score {sig.filter_score.toFixed(2)}</span>}
              </div>
            </button>
          ))}
        </div>
      </div>
    </Card>
  );
}
