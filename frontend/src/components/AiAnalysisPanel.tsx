import { Brain, MapPin, ShieldAlert, Sparkles } from "lucide-react";
import type { AnalysisResult } from "../types";
import { Button, Card, EmptyState, Field } from "./ui";
import { RiskBadge, Tag } from "./Badges";

export function AiAnalysisPanel({
  analysis,
  canAnalyze,
  onAnalyze,
  analyzing,
}: {
  analysis: AnalysisResult | null;
  canAnalyze: boolean;
  onAnalyze: () => void;
  analyzing: boolean;
}) {
  return (
    <Card
      title="Gemini Analysis"
      icon={<Brain className="h-4 w-4 text-cyan-400" />}
      actions={
        <Button variant="primary" onClick={onAnalyze} loading={analyzing} disabled={!canAnalyze} icon={<Sparkles className="h-4 w-4" />}>
          Run Gemini Analysis
        </Button>
      }
    >
      {analyzing && <EmptyState>Analyzing with Gemini… this can take a few seconds.</EmptyState>}

      {!analyzing && !analysis && (
        <EmptyState>
          {canAnalyze
            ? "Signal released. Click “Run Gemini Analysis” to extract a structured event."
            : "Release a signal first, then run Gemini analysis."}
        </EmptyState>
      )}

      {!analyzing && analysis && analysis.outcome === "rejected" && (
        <div className="space-y-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
          <div className="flex items-center gap-2 text-amber-300">
            <ShieldAlert className="h-4 w-4" />
            <span className="text-sm font-semibold">Signal rejected as low operational relevance</span>
          </div>
          <Field label="Rejection Reason" value={analysis.rejection_reason} />
          {analysis.reasoning_brief && <Field label="Reasoning" value={analysis.reasoning_brief} />}
          <p className="text-xs text-slate-500">This is expected behavior — not every public signal is operationally relevant.</p>
        </div>
      )}

      {!analyzing && analysis && analysis.outcome === "accepted" && (
        <div className="space-y-4">
          <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-2 text-center text-xs font-medium text-emerald-300">
            Structured Event Created · ID #{analysis.event_id}
          </div>

          <h3 className="text-base font-semibold leading-snug text-white">{analysis.title}</h3>

          <div className="flex flex-wrap items-center gap-2">
            {analysis.event_type && <Tag>{analysis.event_type}</Tag>}
            <RiskBadge level={analysis.severity} />
            {analysis.confidence != null && <Tag>confidence {(analysis.confidence * 100).toFixed(0)}%</Tag>}
          </div>

          {analysis.summary && <p className="text-sm leading-relaxed text-slate-300">{analysis.summary}</p>}

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <Field
              label="Location"
              value={
                analysis.location_name ? (
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-slate-500" />
                    {analysis.location_name}
                  </span>
                ) : null
              }
            />
            <Field
              label="Coordinates"
              value={
                analysis.latitude != null
                  ? `${analysis.latitude.toFixed(3)}, ${analysis.longitude?.toFixed(3)}`
                  : null
              }
            />
          </div>

          <div className="space-y-3 rounded-lg bg-ink-900/50 p-3">
            <Field label="Business Impact" value={analysis.business_impact} />
            <Field label="Recommended Action" value={analysis.recommended_action} />
            {analysis.reasoning_brief && <Field label="Reasoning Brief" value={analysis.reasoning_brief} />}
          </div>
        </div>
      )}
    </Card>
  );
}
