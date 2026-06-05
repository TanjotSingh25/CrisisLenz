import { useState } from "react";
import { ChevronDown, ExternalLink, FileText } from "lucide-react";
import type { ReplaySignal } from "../types";
import { Card, EmptyState, Field } from "./ui";
import { SourceBadge, Tag } from "./Badges";

export function CurrentSignalCard({ signal }: { signal: ReplaySignal | null }) {
  const [showRaw, setShowRaw] = useState(false);

  if (!signal)
    return (
      <Card title="Raw Incoming Signal" icon={<FileText className="h-4 w-4 text-cyan-400" />}>
        <EmptyState>Release a signal to begin. The raw incoming signal will appear here.</EmptyState>
      </Card>
    );

  const isEonet = signal.source_type === "eonet_event";

  return (
    <Card title="Raw Incoming Signal" icon={<FileText className="h-4 w-4 text-cyan-400" />}>
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <SourceBadge sourceType={signal.source_type} />
          <span className="text-xs text-slate-500">{signal.source_name}</span>
        </div>

        <h3 className="text-base font-semibold leading-snug text-white">{signal.title}</h3>

        {signal.summary && <p className="text-sm leading-relaxed text-slate-300">{signal.summary}</p>}

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {signal.category_hint && <Field label="Category" value={signal.category_hint} />}
          {signal.filter_score != null && <Field label="Filter Score" value={signal.filter_score.toFixed(2)} />}
          {isEonet && <Field label="Event Category" value={signal.event_category} />}
          {isEonet && <Field label="Event Status" value={signal.event_status} />}
          {isEonet && signal.latitude != null && (
            <Field label="Coordinates" value={`${signal.latitude.toFixed(3)}, ${signal.longitude?.toFixed(3)}`} />
          )}
        </div>

        {signal.matched_keywords && signal.matched_keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {signal.matched_keywords.map((kw) => (
              <Tag key={kw}>{kw}</Tag>
            ))}
          </div>
        )}

        {signal.url && (
          <a
            href={signal.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300"
          >
            <ExternalLink className="h-3 w-3" /> Source Evidence
          </a>
        )}

        <div>
          <button
            onClick={() => setShowRaw((v) => !v)}
            className="inline-flex items-center gap-1 text-[11px] text-slate-500 hover:text-slate-300"
          >
            <ChevronDown className={`h-3 w-3 transition-transform ${showRaw ? "rotate-180" : ""}`} /> Developer details
          </button>
          {showRaw && (
            <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-ink-900 p-3 text-[11px] text-slate-400">
              {JSON.stringify(signal, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </Card>
  );
}
