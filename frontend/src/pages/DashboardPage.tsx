import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Eraser, Play, Square } from "lucide-react";
import { Header } from "../components/Header";
import { WorkflowStepper } from "../components/WorkflowStepper";
import { SignalQueuePanel } from "../components/SignalQueuePanel";
import { CurrentSignalCard } from "../components/CurrentSignalCard";
import { AiAnalysisPanel } from "../components/AiAnalysisPanel";
import { ImpactPanel } from "../components/ImpactPanel";
import { AlertPanel } from "../components/AlertPanel";
import { Button } from "../components/ui";
import { ToastProvider, useToast } from "../components/Toast";
import { ApiError } from "../api/client";
import { aiApi, alertsApi, clientsApi, impactApi, replayApi } from "../api";
import type {
  Alert,
  AnalysisResult,
  ClientAsset,
  MatchEventResponse,
  ReplaySignal,
  ReplayStatus,
  StepStatus,
  WorkflowStepKey,
} from "../types";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function Dashboard() {
  const toast = useToast();

  const [status, setStatus] = useState<ReplayStatus | null>(null);
  const [pending, setPending] = useState<ReplaySignal[]>([]);
  const [allAssets, setAllAssets] = useState<ClientAsset[]>([]);
  const [source, setSource] = useState("all");

  const [releasedSignal, setReleasedSignal] = useState<ReplaySignal | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [match, setMatch] = useState<MatchEventResponse | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const [signalCollapsed, setSignalCollapsed] = useState(false);
  const [releasing, setReleasing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [matching, setMatching] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [busyAlertId, setBusyAlertId] = useState<number | null>(null);
  const [autoRunning, setAutoRunning] = useState(false);
  const autoStop = useRef(false);

  const handleError = useCallback(
    (e: unknown, fallback: string) => {
      const msg = e instanceof ApiError ? e.message : fallback;
      toast("error", msg);
    },
    [toast]
  );

  const refreshStatus = useCallback(async () => {
    try {
      const [s, p] = await Promise.all([replayApi.status(), replayApi.pending(source)]);
      setStatus(s);
      setPending(p);
    } catch (e) {
      handleError(e, "Failed to load replay status.");
    }
  }, [source, handleError]);

  useEffect(() => {
    refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    clientsApi
      .allAssets()
      .then(setAllAssets)
      .catch(() => setAllAssets([]));
  }, []);

  const resetDemoView = () => {
    setReleasedSignal(null);
    setAnalysis(null);
    setMatch(null);
    setAlerts([]);
    setSignalCollapsed(false);
    toast("info", "Demo view cleared. Backend state untouched.");
  };

  // --- Pipeline steps -------------------------------------------------------

  const releaseSignal = useCallback(
    async (specific?: ReplaySignal): Promise<ReplaySignal | null> => {
      setReleasing(true);
      setAnalysis(null);
      setMatch(null);
      setAlerts([]);
      setSignalCollapsed(false); // expand the raw signal for the new item
      try {
        const sig = specific
          ? await replayApi.releaseSpecific(specific.id)
          : await replayApi.releaseNext(source);
        setReleasedSignal(sig);
        toast("success", `Released signal #${sig.id}.`);
        await refreshStatus();
        return sig;
      } catch (e) {
        handleError(e, "Failed to release a signal.");
        return null;
      } finally {
        setReleasing(false);
      }
    },
    [source, toast, refreshStatus, handleError]
  );

  const analyze = useCallback(
    async (sig: ReplaySignal | null): Promise<AnalysisResult | null> => {
      if (!sig) return null;
      setAnalyzing(true);
      try {
        const result = await aiApi.analyzeSignal(sig.id);
        setAnalysis(result);
        setSignalCollapsed(true); // collapse raw signal once analysis is in
        if (result.outcome === "accepted") toast("success", "Event created from signal.");
        else toast("info", "Signal rejected as low operational relevance.");
        await refreshStatus();
        return result;
      } catch (e) {
        handleError(e, "Gemini analysis failed. Check backend logs or API key.");
        return null;
      } finally {
        setAnalyzing(false);
      }
    },
    [toast, refreshStatus, handleError]
  );

  const runMatch = useCallback(
    async (eventId: number | null | undefined): Promise<MatchEventResponse | null> => {
      if (!eventId) return null;
      setMatching(true);
      try {
        const result = await impactApi.matchEvent(eventId);
        setMatch(result);
        if (result.skipped) toast("info", result.skip_reason ?? "Impact matching skipped.");
        else toast("success", `${result.total_matches} affected asset(s) found.`);
        return result;
      } catch (e) {
        handleError(e, "Impact matching failed.");
        return null;
      } finally {
        setMatching(false);
      }
    },
    [toast, handleError]
  );

  const generateAlerts = useCallback(
    async (eventId: number | null | undefined): Promise<Alert[]> => {
      if (!eventId) return [];
      setGenerating(true);
      try {
        const res = await alertsApi.generateForEvent(eventId);
        const list = await alertsApi.listForEvent(eventId);
        setAlerts(list);
        toast("success", `${res.alerts_created} alert(s) created, ${res.alerts_skipped} skipped.`);
        return list;
      } catch (e) {
        handleError(e, "Alert generation failed.");
        return [];
      } finally {
        setGenerating(false);
      }
    },
    [toast, handleError]
  );

  const acknowledge = async (id: number) => {
    setBusyAlertId(id);
    try {
      const updated = await alertsApi.acknowledge(id);
      setAlerts((a) => a.map((x) => (x.id === id ? updated : x)));
    } catch (e) {
      handleError(e, "Could not acknowledge alert.");
    } finally {
      setBusyAlertId(null);
    }
  };

  const dismiss = async (id: number) => {
    setBusyAlertId(id);
    try {
      const updated = await alertsApi.dismiss(id);
      setAlerts((a) => a.map((x) => (x.id === id ? updated : x)));
    } catch (e) {
      handleError(e, "Could not dismiss alert.");
    } finally {
      setBusyAlertId(null);
    }
  };

  const resetReplay = async () => {
    try {
      const res = await replayApi.reset(source);
      toast("success", res.message);
      resetDemoView();
      await refreshStatus();
    } catch (e) {
      handleError(e, "Failed to reset replay.");
    }
  };

  // --- Auto demo ------------------------------------------------------------

  const runAutoDemo = async () => {
    autoStop.current = false;
    setAutoRunning(true);
    try {
      const sig = await releaseSignal();
      if (autoStop.current || !sig) return;
      await sleep(900);

      const res = await analyze(sig);
      if (autoStop.current || !res || res.outcome !== "accepted") return;
      await sleep(900);

      const m = await runMatch(res.event_id);
      if (autoStop.current || !m || m.skipped || m.total_matches === 0) return;
      await sleep(900);

      await generateAlerts(res.event_id);
    } finally {
      setAutoRunning(false);
    }
  };

  const stopAutoDemo = () => {
    autoStop.current = true;
    setAutoRunning(false);
  };

  // --- Step statuses --------------------------------------------------------

  const steps = useMemo<Record<WorkflowStepKey, StepStatus>>(() => {
    const accepted = analysis?.outcome === "accepted";
    const rejected = analysis?.outcome === "rejected";
    return {
      signal_intake: releasing ? "active" : releasedSignal ? "completed" : "not_started",
      analysis: analyzing ? "active" : rejected ? "rejected" : accepted ? "completed" : "not_started",
      event_created: rejected ? "rejected" : accepted ? "completed" : "not_started",
      impact_matching: matching ? "active" : match ? (match.skipped ? "rejected" : "completed") : "not_started",
      alert_generation: generating ? "active" : alerts.length > 0 ? "completed" : "not_started",
    };
  }, [releasing, releasedSignal, analyzing, analysis, matching, match, generating, alerts]);

  const accepted = analysis?.outcome === "accepted";
  const hasMatches = !!match && !match.skipped && match.total_matches > 0;

  return (
    <div className="flex min-h-screen flex-col">
      <Header status={status} alertCount={alerts.length} />

      <div className="flex flex-col gap-4 p-4 lg:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="flex-1">
            <WorkflowStepper statuses={steps} />
          </div>
          <div className="flex gap-2">
            {autoRunning ? (
              <Button variant="danger" onClick={stopAutoDemo} icon={<Square className="h-4 w-4" />}>
                Stop Auto Demo
              </Button>
            ) : (
              <Button variant="subtle" onClick={runAutoDemo} icon={<Play className="h-4 w-4" />}>
                Auto-run Demo
              </Button>
            )}
            <Button variant="ghost" onClick={resetDemoView} icon={<Eraser className="h-4 w-4" />}>
              Clear View
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
          {/* Left column */}
          <div className="lg:col-span-3">
            <SignalQueuePanel
              pending={pending}
              source={source}
              onSourceChange={setSource}
              onReleaseNext={() => releaseSignal()}
              onReleaseSpecific={(s) => releaseSignal(s)}
              onReset={resetReplay}
              onRefresh={refreshStatus}
              busy={releasing}
            />
          </div>

          {/* Center column */}
          <div className="flex flex-col gap-4 lg:col-span-5">
            <CurrentSignalCard
              signal={releasedSignal}
              collapsed={signalCollapsed}
              onToggleCollapse={() => setSignalCollapsed((v) => !v)}
            />
            <AiAnalysisPanel
              analysis={analysis}
              canAnalyze={!!releasedSignal && !analysis}
              onAnalyze={() => analyze(releasedSignal)}
              analyzing={analyzing}
            />
          </div>

          {/* Right column */}
          <div className="flex flex-col gap-4 lg:col-span-4">
            <ImpactPanel
              match={match}
              allAssets={allAssets}
              canMatch={accepted}
              onMatch={() => runMatch(analysis?.event_id)}
              matching={matching}
            />
            <AlertPanel
              alerts={alerts}
              canGenerate={hasMatches}
              onGenerate={() => generateAlerts(analysis?.event_id)}
              generating={generating}
              onAcknowledge={acknowledge}
              onDismiss={dismiss}
              busyAlertId={busyAlertId}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  return (
    <ToastProvider>
      <Dashboard />
    </ToastProvider>
  );
}
