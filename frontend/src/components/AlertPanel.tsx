import { BellRing, Check, Send, X } from "lucide-react";
import type { Alert } from "../types";
import { Button, Card, EmptyState } from "./ui";
import { RiskBadge, StatusBadge } from "./Badges";

export function AlertPanel({
  alerts,
  canGenerate,
  onGenerate,
  generating,
  onAcknowledge,
  onDismiss,
  busyAlertId,
}: {
  alerts: Alert[];
  canGenerate: boolean;
  onGenerate: () => void;
  generating: boolean;
  onAcknowledge: (id: number) => void;
  onDismiss: (id: number) => void;
  busyAlertId: number | null;
}) {
  return (
    <Card
      title="Simulated Client Alerts"
      icon={<BellRing className="h-4 w-4 text-cyan-400" />}
      actions={
        <Button variant="primary" onClick={onGenerate} loading={generating} disabled={!canGenerate} icon={<Send className="h-4 w-4" />}>
          Generate Simulated Alerts
        </Button>
      }
    >
      {alerts.length === 0 && (
        <EmptyState>
          {canGenerate
            ? "Impact matches found. Generate simulated client alerts."
            : "Run impact matching with at least one affected asset to generate alerts."}
        </EmptyState>
      )}

      <div className="space-y-2.5">
        {alerts.map((alert) => {
          const terminal = alert.status === "dismissed";
          return (
            <div key={alert.id} className="rounded-lg border border-ink-600 bg-ink-800 p-3">
              <div className="mb-1.5 flex items-start justify-between gap-2">
                <span className="text-sm font-semibold leading-snug text-white">{alert.alert_title}</span>
                <div className="flex shrink-0 items-center gap-1.5">
                  <RiskBadge level={alert.risk_level} />
                  <StatusBadge status={alert.status} />
                </div>
              </div>

              <div className="mb-2 text-xs text-slate-400">
                {alert.client} — {alert.asset}
                {alert.distance_km != null && <span className="text-slate-500"> · {alert.distance_km} km from event</span>}
              </div>

              {alert.alert_summary && <p className="mb-2 text-xs leading-relaxed text-slate-300">{alert.alert_summary}</p>}

              {alert.recommended_action && (
                <div className="mb-2 rounded-md bg-ink-900/50 p-2">
                  <div className="text-[10px] uppercase tracking-wide text-slate-500">Recommended Action</div>
                  <div className="text-xs text-slate-300">{alert.recommended_action}</div>
                </div>
              )}

              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500">
                  {alert.delivery_channel} · {alert.delivery_status}
                </span>
                <div className="flex gap-1.5">
                  <Button
                    variant="ghost"
                    className="px-2 py-1 text-xs"
                    disabled={alert.status === "acknowledged" || terminal}
                    loading={busyAlertId === alert.id}
                    onClick={() => onAcknowledge(alert.id)}
                    icon={<Check className="h-3 w-3" />}
                  >
                    Acknowledge
                  </Button>
                  <Button
                    variant="ghost"
                    className="px-2 py-1 text-xs"
                    disabled={terminal}
                    loading={busyAlertId === alert.id}
                    onClick={() => onDismiss(alert.id)}
                    icon={<X className="h-3 w-3" />}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {alerts.length > 0 && (
        <p className="mt-3 text-center text-[10px] text-slate-600">Simulated dashboard alerts — not sent externally.</p>
      )}
    </Card>
  );
}
