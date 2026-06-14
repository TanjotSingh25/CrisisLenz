// Mirrors the backend Pydantic schemas. Keep in sync with the FastAPI responses.

export interface SourceTypeStatusCounts {
  pending: number;
  released: number;
  processed: number;
  rejected: number;
}

export interface ReplayStatus {
  total: number;
  pending: number;
  released: number;
  processed: number;
  rejected: number;
  by_source_type: Record<string, SourceTypeStatusCounts>;
}

export interface ReplaySignal {
  id: number;
  source_type: string | null;
  source_name: string | null;
  title: string | null;
  published_at: string | null;
  summary: string | null;
  body: string | null;
  language: string | null;
  url: string | null;
  filter_score: number | null;
  category_hint: string | null;
  matched_keywords: string[] | null;
  status: string;
  release_order: number | null;
  released_at: string | null;
  processed_at: string | null;
  latitude: number | null;
  longitude: number | null;
  event_category: string | null;
  event_status: string | null;
  created_at: string;
  updated_at: string;
}

// AnalysisResponse from /ai/analyze-signal/{id}
export interface AnalysisResult {
  signal_id: number | null;
  outcome: string; // "accepted" | "rejected"
  analysis_id: number;
  is_event_worthy: boolean;
  event_type: string | null;
  severity: string | null;
  confidence: number | null;
  title: string | null;
  summary: string | null;
  location_name: string | null;
  latitude: number | null;
  longitude: number | null;
  business_impact: string | null;
  recommended_action: string | null;
  reasoning_brief: string | null;
  event_id: number | null;
  rejection_reason: string | null;
}

export interface AffectedAsset {
  impact_id: number;
  client: string;
  asset: string;
  asset_type: string | null;
  city: string | null;
  country: string | null;
  latitude: number;
  longitude: number;
  criticality: string;
  distance_km: number;
  impact_radius_km: number;
  risk_level: string | null;
  match_reason: string | null;
}

export interface MatchEventResponse {
  event_id: number;
  event_title: string | null;
  event_type: string | null;
  severity: string | null;
  latitude: number | null;
  longitude: number | null;
  impact_radius_km: number | null;
  assets_evaluated: number;
  nearest_km: number | null;
  matches_created: number;
  total_matches: number;
  skipped: boolean;
  skip_reason: string | null;
  affected_assets: AffectedAsset[];
}

export interface ClientAsset {
  id: number;
  client_id: number;
  name: string;
  asset_type: string | null;
  latitude: number;
  longitude: number;
  city: string | null;
  region: string | null;
  country: string | null;
  criticality: string;
  created_at: string;
}

export interface Alert {
  id: number;
  event_id: number;
  client_id: number;
  client_asset_id: number;
  event_asset_impact_id: number;
  client: string | null;
  asset: string | null;
  asset_type: string | null;
  event_title: string | null;
  event_type: string | null;
  alert_title: string | null;
  alert_summary: string | null;
  recommended_action: string | null;
  risk_level: string | null;
  status: string;
  delivery_channel: string;
  delivery_status: string;
  distance_km: number | null;
  impact_radius_km: number | null;
  created_at: string;
  updated_at: string;
  acknowledged_at: string | null;
  dismissed_at: string | null;
}

export interface GenerateForEventResponse {
  event_id: number;
  event_title: string | null;
  impacts_found: number;
  alerts_created: number;
  alerts_skipped: number;
  alerts: { id: number; client: string | null; asset: string | null; risk_level: string | null; status: string }[];
}

export type StepStatus = "not_started" | "active" | "completed" | "rejected" | "failed";

export type WorkflowStepKey =
  | "signal_intake"
  | "analysis"
  | "event_created"
  | "impact_matching"
  | "alert_generation";
