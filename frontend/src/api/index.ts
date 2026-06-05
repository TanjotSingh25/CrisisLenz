import { api } from "./client";
import type {
  Alert,
  AnalysisResult,
  ClientAsset,
  GenerateForEventResponse,
  MatchEventResponse,
  ReplaySignal,
  ReplayStatus,
} from "../types";

const src = (sourceType?: string) =>
  sourceType && sourceType !== "all" ? `?source_type=${encodeURIComponent(sourceType)}` : "";

export const replayApi = {
  status: () => api.get<ReplayStatus>("/replay/status"),
  pending: (sourceType?: string) => api.get<ReplaySignal[]>(`/replay/signals/pending${src(sourceType)}`),
  released: (sourceType?: string) => api.get<ReplaySignal[]>(`/replay/signals/released${src(sourceType)}`),
  releaseNext: (sourceType?: string) => api.post<ReplaySignal>(`/replay/next${src(sourceType)}`),
  releaseSpecific: (signalId: number) => api.post<ReplaySignal>(`/replay/release/${signalId}`),
  reset: (sourceType?: string) => api.post<{ message: string }>(`/replay/reset${src(sourceType)}`),
  reseed: () => api.post<{ message: string }>("/replay/reseed"),
};

export const aiApi = {
  analyzeSignal: (signalId: number) => api.post<AnalysisResult>(`/ai/analyze-signal/${signalId}`),
};

export const impactApi = {
  matchEvent: (eventId: number) => api.post<MatchEventResponse>(`/impact/match-event/${eventId}`),
  getEvent: (eventId: number) => api.get<MatchEventResponse>(`/impact/event/${eventId}`),
  rules: () => api.get<Record<string, Record<string, number>>>("/impact/rules"),
};

export const clientsApi = {
  seed: () => api.post<{ clients_seeded: number; assets_seeded: number }>("/clients/seed"),
  allAssets: () => api.get<ClientAsset[]>("/clients/assets/all"),
};

export const alertsApi = {
  generateForEvent: (eventId: number) =>
    api.post<GenerateForEventResponse>(`/alerts/generate-for-event/${eventId}`),
  listForEvent: (eventId: number) => api.get<Alert[]>(`/alerts?event_id=${eventId}`),
  list: () => api.get<Alert[]>("/alerts"),
  acknowledge: (alertId: number) => api.post<Alert>(`/alerts/${alertId}/acknowledge`),
  dismiss: (alertId: number) => api.post<Alert>(`/alerts/${alertId}/dismiss`),
};
