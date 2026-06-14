import { useEffect } from "react";
import { Circle, CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import type { AffectedAsset, ClientAsset, MatchEventResponse } from "../types";

function Recenter({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    map.setView([lat, lng], map.getZoom() < 4 ? 5 : map.getZoom());
  }, [lat, lng, map]);
  return null;
}

export function ImpactMap({
  match,
  allAssets,
}: {
  match: MatchEventResponse | null;
  allAssets: ClientAsset[];
}) {
  const hasEvent = match && match.latitude != null && match.longitude != null;
  const center: [number, number] = hasEvent ? [match!.latitude!, match!.longitude!] : [20, 0];

  const isMatched = (assetName: string) =>
    (match?.affected_assets ?? []).some((a: AffectedAsset) => a.asset === assetName);

  const matchedAssets = allAssets.filter((a) => isMatched(a.name));
  const unmatchedAssets = allAssets.filter((a) => !isMatched(a.name));

  const renderAsset = (a: ClientAsset, matched: boolean) => (
    <CircleMarker
      key={a.id}
      center={[a.latitude, a.longitude]}
      radius={matched ? 9 : 5}
      pathOptions={{
        color: matched ? "#fca5a5" : "#38bdf8",
        fillColor: matched ? "#ef4444" : "#0ea5e9",
        fillOpacity: matched ? 0.95 : 0.5,
        weight: matched ? 2 : 1,
      }}
    >
      <Popup>
        <div className="space-y-0.5 text-xs">
          <div className="font-semibold text-white">{a.name}</div>
          <div className="text-slate-300">
            {a.city}
            {a.country ? `, ${a.country}` : ""}
          </div>
          <div className={matched ? "text-red-300" : "text-slate-400"}>
            {matched ? "Affected client asset" : "Client asset"}
          </div>
        </div>
      </Popup>
    </CircleMarker>
  );

  return (
    <div className="h-[360px] overflow-hidden rounded-lg border border-ink-600">
      <MapContainer center={center} zoom={hasEvent ? 5 : 2} className="h-full w-full" worldCopyJump>
        {/* Esri dark-gray canvas — English/Latin labels. Base is dimmed via CSS;
            the reference (labels) layer is kept crisp on top. */}
        <TileLayer
          className="basemap-dim"
          attribution="&copy; Esri"
          url="https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        />
        <TileLayer
          attribution=""
          url="https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
        />
        {hasEvent && <Recenter lat={match!.latitude!} lng={match!.longitude!} />}

        {/* Estimated operational impact zone. interactive:false so it never
            steals clicks meant for the asset markers sitting on top of it. */}
        {hasEvent && match!.impact_radius_km && (
          <Circle
            center={center}
            radius={match!.impact_radius_km * 1000}
            pathOptions={{ color: "#f59e0b", fillColor: "#f59e0b", fillOpacity: 0.08, weight: 1, interactive: false }}
          >
            <Tooltip>Estimated Operational Impact Zone ({match!.impact_radius_km} km)</Tooltip>
          </Circle>
        )}

        {/* Unmatched assets first (lowest). */}
        {unmatchedAssets.map((a) => renderAsset(a, false))}

        {/* Event marker — non-interactive so clicks pass through to any matched
            asset underneath it. Hover tooltip still names the event. */}
        {hasEvent && (
          <CircleMarker
            center={center}
            radius={12}
            pathOptions={{ color: "#fcd34d", fillColor: "#f59e0b", fillOpacity: 0.3, weight: 3, interactive: false }}
          >
            <Tooltip>Event: {match!.event_title}</Tooltip>
          </CircleMarker>
        )}

        {/* Matched (affected) assets rendered LAST = topmost and fully clickable. */}
        {matchedAssets.map((a) => renderAsset(a, true))}
      </MapContainer>
      {!hasEvent && (
        <div className="-mt-[360px] grid h-[360px] place-items-center bg-ink-900/70 text-center text-sm text-slate-500">
          <span>Run impact matching on an event with coordinates to see the map.</span>
        </div>
      )}
    </div>
  );
}
