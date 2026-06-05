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

  return (
    <div className="h-[360px] overflow-hidden rounded-lg border border-ink-600">
      <MapContainer center={center} zoom={hasEvent ? 5 : 2} className="h-full w-full" worldCopyJump>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        {hasEvent && <Recenter lat={match!.latitude!} lng={match!.longitude!} />}

        {/* Estimated operational impact zone */}
        {hasEvent && match!.impact_radius_km && (
          <Circle
            center={center}
            radius={match!.impact_radius_km * 1000}
            pathOptions={{ color: "#f59e0b", fillColor: "#f59e0b", fillOpacity: 0.08, weight: 1 }}
          >
            <Tooltip>Estimated Operational Impact Zone ({match!.impact_radius_km} km)</Tooltip>
          </Circle>
        )}

        {/* All client assets */}
        {allAssets.map((a) => {
          const matched = isMatched(a.name);
          return (
            <CircleMarker
              key={a.id}
              center={[a.latitude, a.longitude]}
              radius={matched ? 8 : 5}
              pathOptions={{
                color: matched ? "#f87171" : "#38bdf8",
                fillColor: matched ? "#ef4444" : "#0ea5e9",
                fillOpacity: matched ? 0.9 : 0.5,
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
                  <div className="text-slate-400">{matched ? "Affected client asset" : "Client asset"}</div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}

        {/* Event marker on top */}
        {hasEvent && (
          <CircleMarker
            center={center}
            radius={9}
            pathOptions={{ color: "#fde68a", fillColor: "#f59e0b", fillOpacity: 1, weight: 2 }}
          >
            <Popup>
              <div className="space-y-0.5 text-xs">
                <div className="font-semibold text-white">Event location</div>
                <div className="text-slate-300">{match!.event_title}</div>
              </div>
            </Popup>
          </CircleMarker>
        )}
      </MapContainer>
      {!hasEvent && (
        <div className="-mt-[360px] grid h-[360px] place-items-center bg-ink-900/70 text-center text-sm text-slate-500">
          <span>Run impact matching on an event with coordinates to see the map.</span>
        </div>
      )}
    </div>
  );
}
