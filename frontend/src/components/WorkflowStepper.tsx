import { Check, CircleDashed, Loader2, X } from "lucide-react";
import type { StepStatus, WorkflowStepKey } from "../types";

const STEPS: { key: WorkflowStepKey; label: string }[] = [
  { key: "signal_intake", label: "Signal Intake" },
  { key: "analysis", label: "Gemini Analysis" },
  { key: "event_created", label: "Event Creation" },
  { key: "impact_matching", label: "Impact Matching" },
  { key: "alert_generation", label: "Alert Generation" },
];

function StepIcon({ status }: { status: StepStatus }) {
  if (status === "completed") return <Check className="h-4 w-4" />;
  if (status === "active") return <Loader2 className="h-4 w-4 animate-spin" />;
  if (status === "rejected" || status === "failed") return <X className="h-4 w-4" />;
  return <CircleDashed className="h-4 w-4" />;
}

const RING: Record<StepStatus, string> = {
  not_started: "bg-ink-700 text-slate-500 ring-ink-600",
  active: "bg-cyan-600/20 text-cyan-300 ring-cyan-500/50",
  completed: "bg-emerald-600/20 text-emerald-300 ring-emerald-500/50",
  rejected: "bg-amber-600/20 text-amber-300 ring-amber-500/50",
  failed: "bg-red-600/20 text-red-300 ring-red-500/50",
};

export function WorkflowStepper({ statuses }: { statuses: Record<WorkflowStepKey, StepStatus> }) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto rounded-xl border border-ink-600 bg-ink-800/80 px-3 py-3">
      {STEPS.map((step, i) => {
        const st = statuses[step.key];
        return (
          <div key={step.key} className="flex flex-1 items-center gap-1">
            <div className="flex min-w-0 flex-col items-center gap-1.5 px-1">
              <div className={`grid h-8 w-8 place-items-center rounded-full ring-1 ${RING[st]}`}>
                <StepIcon status={st} />
              </div>
              <span
                className={`whitespace-nowrap text-[11px] font-medium ${
                  st === "not_started" ? "text-slate-500" : "text-slate-300"
                }`}
              >
                {i + 1}. {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`h-px flex-1 ${
                  statuses[STEPS[i + 1].key] !== "not_started" ? "bg-cyan-600/40" : "bg-ink-600"
                }`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
