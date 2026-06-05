import logging

from sqlalchemy.orm import Session

from app.clients.models import Client, ClientAsset
from app.events.models import Event
from app.impact.haversine import haversine_km
from app.impact.models import EventAssetImpact
from app.impact.rules import get_impact_radius_km
from app.impact.schemas import AffectedAssetOut, MatchEventResponse

logger = logging.getLogger(__name__)


def match_event(db: Session, event_id: int) -> MatchEventResponse:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError(f"Event {event_id} not found.")

    if event.latitude is None or event.longitude is None:
        logger.info("Event %d has no coordinates — skipping impact match.", event_id)
        return MatchEventResponse(
            event_id=event_id,
            event_title=event.title,
            event_type=event.event_type,
            severity=event.severity,
            latitude=None,
            longitude=None,
            impact_radius_km=None,
            matches_created=0,
            total_matches=_count_existing_matches(db, event_id),
            skipped=True,
            skip_reason="Event has no coordinates. Gemini could not determine location.",
        )

    radius_km = get_impact_radius_km(event.event_type, event.severity)
    assets = db.query(ClientAsset).all()

    # Build set of already-matched asset IDs to avoid duplicates
    existing_asset_ids = {
        row.client_asset_id
        for row in db.query(EventAssetImpact.client_asset_id)
        .filter(EventAssetImpact.event_id == event_id)
        .all()
    }

    nearest_km: float | None = None
    new_impacts: list[EventAssetImpact] = []
    for asset in assets:
        distance = haversine_km(event.latitude, event.longitude, asset.latitude, asset.longitude)
        if nearest_km is None or distance < nearest_km:
            nearest_km = distance
        if distance > radius_km:
            continue
        if asset.id in existing_asset_ids:
            continue

        reason = (
            f"Within {radius_km:.0f}km estimated operational impact zone "
            f"({event.severity or 'unknown'}-severity {event.event_type or 'event'})."
        )
        new_impacts.append(EventAssetImpact(
            event_id=event_id,
            client_id=asset.client_id,
            client_asset_id=asset.id,
            distance_km=round(distance, 2),
            impact_radius_km=radius_km,
            risk_level=event.severity,
            match_reason=reason,
        ))

    db.add_all(new_impacts)
    db.commit()

    logger.info(
        "Event %d (%s): radius=%.0fkm, new_matches=%d",
        event_id, event.event_type, radius_km, len(new_impacts),
    )

    affected = _build_affected_list(db, event_id)
    return MatchEventResponse(
        event_id=event_id,
        event_title=event.title,
        event_type=event.event_type,
        severity=event.severity,
        latitude=event.latitude,
        longitude=event.longitude,
        impact_radius_km=radius_km,
        assets_evaluated=len(assets),
        nearest_km=round(nearest_km, 2) if nearest_km is not None else None,
        matches_created=len(new_impacts),
        total_matches=len(affected),
        affected_assets=affected,
    )


def match_unmatched_events(db: Session) -> list[MatchEventResponse]:
    matched_event_ids = {
        row.event_id for row in db.query(EventAssetImpact.event_id).distinct().all()
    }
    unmatched = (
        db.query(Event)
        .filter(Event.id.notin_(matched_event_ids))
        .filter(Event.latitude.isnot(None))
        .all()
    )
    return [match_event(db, e.id) for e in unmatched]


def get_event_impacts(db: Session, event_id: int) -> MatchEventResponse:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError(f"Event {event_id} not found.")

    radius_km = get_impact_radius_km(event.event_type, event.severity) if event.latitude else None
    affected = _build_affected_list(db, event_id)
    return MatchEventResponse(
        event_id=event_id,
        event_title=event.title,
        event_type=event.event_type,
        severity=event.severity,
        latitude=event.latitude,
        longitude=event.longitude,
        impact_radius_km=radius_km,
        matches_created=0,
        total_matches=len(affected),
        affected_assets=affected,
    )


def _count_existing_matches(db: Session, event_id: int) -> int:
    return db.query(EventAssetImpact).filter(EventAssetImpact.event_id == event_id).count()


def _build_affected_list(db: Session, event_id: int) -> list[AffectedAssetOut]:
    rows = db.query(EventAssetImpact).filter(EventAssetImpact.event_id == event_id).all()
    result = []
    for row in rows:
        asset = db.query(ClientAsset).filter(ClientAsset.id == row.client_asset_id).first()
        client = db.query(Client).filter(Client.id == row.client_id).first()
        if asset and client:
            result.append(AffectedAssetOut(
                impact_id=row.id,
                client=client.name,
                asset=asset.name,
                asset_type=asset.asset_type,
                city=asset.city,
                country=asset.country,
                latitude=asset.latitude,
                longitude=asset.longitude,
                criticality=asset.criticality,
                distance_km=row.distance_km,
                impact_radius_km=row.impact_radius_km,
                risk_level=row.risk_level,
                match_reason=row.match_reason,
            ))
    return sorted(result, key=lambda x: x.distance_km)
