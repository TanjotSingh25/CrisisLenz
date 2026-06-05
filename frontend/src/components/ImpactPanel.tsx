import { Crosshair, Target } from "lucide-react";
import type { ClientAsset, MatchEventResponse } from "../types";
import { Button, Card, EmptyState } from "./ui";
import { RiskBadge } from "./Badges";
import { ImpactMap } from "./ImpactMap";

export function ImpactPanel({
  match,
  allAssets,
  canMatch,
  onMatch,
  matching,
}: {
  match: MatchEventResponse | null;
  allAssets: ClientAsset[];
  canMatch: boolean;
  onMatch: () => void;
  matching: boolean;
}) {
  return (
    <Card
      title="Impact Matching"
      icon={<Target className="h-4 w-4 text-cyan-400" />}
      actions={
        <Button variant="primary" onClick={onMatch} loading={matching} disabled={!canMatch} icon={<Crosshair className="h-4 w-4" />}>
          Run Impact Matching
        </Button>
      }
    >
      <div className="space-y-3">
        <ImpactMap match={match} allAssets={allAssets} />

        {!match && (
          <EmptyState>
            {canMatch
              ? "Event ready. Run impact matching to find client assets in the operational impact zone."
              : "Create an event first (accepted Gemini analysis), then run impact matching."}
          </EmptyState>
        )}

        {match && match.skipped && (
          <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-sm text-amber-300">
            {match.skip_reason ?? "Event has no coordinates, so impact matching cannot run."}
          </div>
        )}

        {match && !match.skipped && (
          <>
            <div className="grid grid-cols-3 gap-2 text-center">
              <Stat label="Radius" value={`${match.impact_radius_km ?? "—"} km`} />
              <Stat label="Assets Checked" value={String(match.assets_evaluated)} />
              <Stat label="Matches" value={String(match.total_matches)} accent="text-red-300" />
            </div>

            {match.total_matches === 0 ? (
              <EmptyState>
                No client assets inside the estimated operational impact zone.
                {match.nearest_km != null && ` Nearest asset is ${match.nearest_km} km away.`}
              </EmptyState>
            ) : (
              <div className="space-y-2">
                <div className="text-[11px] uppercase tracking-wide text-slate-500">Affected Client Assets</div>
                {match.affected_assets.map((a) => (
                  <div key={a.impact_id} className="rounded-lg border border-ink-600 bg-ink-800 p-3">
                    <div className="mb-1 flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{a.asset}</span>
                      <RiskBadge level={a.risk_level} />
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-400">
                      <span>{a.client}</span>
                      <span>
                        {a.distance_km} km away · radius {a.impact_radius_km} km
                      </span>
                    </div>
                    <div className="mt-0.5 text-[11px] text-slate-500">
                      {a.city}
                      {a.country ? `, ${a.country}` : ""}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  );
}

function Stat({ label, value, accent = "text-slate-200" }: { label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-lg border border-ink-600 bg-ink-900/50 px-2 py-2">
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-sm font-semibold ${accent}`}>{value}</div>
    </div>
  );
}
