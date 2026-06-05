import logging

from sqlalchemy.orm import Session

from app.alerts.models import ClientAlert
from app.alerts.schemas import AlertOut, GeneratedAlertBrief
from app.clients.models import Client, ClientAsset
from app.common.errors import conflict, not_found
from app.common.timestamps import utcnow
from app.events.models import Event
from app.impact.models import EventAssetImpact

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"new", "acknowledged", "dismissed"}


# ---------------------------------------------------------------------------
# Alert content composition — deterministic, no AI calls
# ---------------------------------------------------------------------------

def _risk_phrase(risk_level: str | None) -> str:
    """Human-readable risk prefix, e.g. 'High-risk'. Falls back gracefully."""
    if not risk_level:
        return "Potential"
    return f"{risk_level.capitalize()}-risk"


def _build_title(event: Event, asset: ClientAsset, risk_level: str | None) -> str:
    """e.g. 'High-risk wildfire near Idaho Field Site'."""
    event_kind = (event.event_type or "incident").replace("_", " ")
    asset_name = asset.name or "client asset"
    return f"{_risk_phrase(risk_level)} {event_kind} near {asset_name}"


def _build_summary(event: Event, client: Client, asset: ClientAsset) -> str:
    """Professional, operational summary. No dramatic language."""
    event_kind = (event.event_type or "event").replace("_", " ")
    location = event.location_name or "the affected area"
    client_name = client.name or "the client"
    asset_name = asset.name or "an asset"
    return (
        f"A {event_kind} near {location} may affect {client_name}'s {asset_name}. "
        f"The asset is within the estimated operational impact zone for this event."
    )


def _default_action(event: Event) -> str:
    """Fallback recommended action when the event has none from Gemini."""
    event_kind = (event.event_type or "event").replace("_", " ")
    return (
        f"Monitor official {event_kind} updates, review employee and site exposure, "
        f"and prepare continuity plans if conditions worsen."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def _create_alert_from_impact(db: Session, impact: EventAssetImpact) -> ClientAlert | None:
    """
    Build one alert from an impact match. Returns None if an alert already
    exists for this (event_id, client_asset_id) pair (duplicate prevention).
    """
    existing = (
        db.query(ClientAlert)
        .filter(
            ClientAlert.event_id == impact.event_id,
            ClientAlert.client_asset_id == impact.client_asset_id,
        )
        .first()
    )
    if existing:
        return None

    event = db.query(Event).filter(Event.id == impact.event_id).first()
    client = db.query(Client).filter(Client.id == impact.client_id).first()
    asset = db.query(ClientAsset).filter(ClientAsset.id == impact.client_asset_id).first()
    if not event or not client or not asset:
        logger.warning(
            "Skipping impact %d — missing event/client/asset reference.", impact.id
        )
        return None

    # Risk level: prefer the impact match's level, fall back to event severity
    risk_level = impact.risk_level or event.severity

    alert = ClientAlert(
        event_id=event.id,
        client_id=client.id,
        client_asset_id=asset.id,
        event_asset_impact_id=impact.id,
        alert_title=_build_title(event, asset, risk_level),
        alert_summary=_build_summary(event, client, asset),
        recommended_action=event.recommended_action or _default_action(event),
        risk_level=risk_level,
        status="new",
        delivery_channel="simulated_dashboard",
        delivery_status="not_sent",
        distance_km=impact.distance_km,
        impact_radius_km=impact.impact_radius_km,
    )
    db.add(alert)
    return alert


def generate_for_event(db: Session, event_id: int) -> dict:
    """Generate alerts for every impact match belonging to one event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise not_found(f"Event {event_id} not found.")

    impacts = (
        db.query(EventAssetImpact)
        .filter(EventAssetImpact.event_id == event_id)
        .all()
    )

    created: list[ClientAlert] = []
    skipped = 0
    for impact in impacts:
        alert = _create_alert_from_impact(db, impact)
        if alert is None:
            skipped += 1
        else:
            created.append(alert)

    db.commit()
    for a in created:
        db.refresh(a)

    return {
        "event_id": event_id,
        "event_title": event.title,
        "impacts_found": len(impacts),
        "alerts_created": len(created),
        "alerts_skipped": skipped,
        "alerts": [_to_brief(db, a) for a in created],
    }


def generate_pending(db: Session) -> dict:
    """Generate alerts for all impact matches that don't yet have an alert."""
    impacts = db.query(EventAssetImpact).all()

    created: list[ClientAlert] = []
    skipped = 0
    for impact in impacts:
        alert = _create_alert_from_impact(db, impact)
        if alert is None:
            skipped += 1
        else:
            created.append(alert)

    db.commit()
    for a in created:
        db.refresh(a)

    return {
        "impacts_found": len(impacts),
        "alerts_created": len(created),
        "alerts_skipped": skipped,
        "alerts": [_to_brief(db, a) for a in created],
    }


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

def list_alerts(
    db: Session,
    status: str | None = None,
    client_id: int | None = None,
    event_id: int | None = None,
    risk_level: str | None = None,
) -> list[AlertOut]:
    query = db.query(ClientAlert)
    if status:
        query = query.filter(ClientAlert.status == status)
    if client_id:
        query = query.filter(ClientAlert.client_id == client_id)
    if event_id:
        query = query.filter(ClientAlert.event_id == event_id)
    if risk_level:
        query = query.filter(ClientAlert.risk_level == risk_level)

    alerts = query.order_by(ClientAlert.created_at.desc()).all()
    return [_to_out(db, a) for a in alerts]


def get_alert(db: Session, alert_id: int) -> AlertOut:
    alert = db.query(ClientAlert).filter(ClientAlert.id == alert_id).first()
    if not alert:
        raise not_found(f"Alert {alert_id} not found.")
    return _to_out(db, alert)


def acknowledge_alert(db: Session, alert_id: int) -> AlertOut:
    alert = db.query(ClientAlert).filter(ClientAlert.id == alert_id).first()
    if not alert:
        raise not_found(f"Alert {alert_id} not found.")
    if alert.status == "dismissed":
        raise conflict(f"Alert {alert_id} is dismissed and cannot be acknowledged.")
    alert.status = "acknowledged"
    alert.acknowledged_at = utcnow()
    db.commit()
    db.refresh(alert)
    return _to_out(db, alert)


def dismiss_alert(db: Session, alert_id: int) -> AlertOut:
    alert = db.query(ClientAlert).filter(ClientAlert.id == alert_id).first()
    if not alert:
        raise not_found(f"Alert {alert_id} not found.")
    alert.status = "dismissed"
    alert.dismissed_at = utcnow()
    db.commit()
    db.refresh(alert)
    return _to_out(db, alert)


def get_summary(db: Session) -> dict:
    alerts = db.query(ClientAlert).all()
    by_risk: dict[str, int] = {}
    counts = {"new": 0, "acknowledged": 0, "dismissed": 0}
    for a in alerts:
        if a.status in counts:
            counts[a.status] += 1
        key = a.risk_level or "unknown"
        by_risk[key] = by_risk.get(key, 0) + 1

    return {
        "total": len(alerts),
        "new": counts["new"],
        "acknowledged": counts["acknowledged"],
        "dismissed": counts["dismissed"],
        "by_risk_level": by_risk,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_brief(db: Session, alert: ClientAlert) -> GeneratedAlertBrief:
    """Compact alert view with resolved client/asset names for generation responses."""
    client = db.query(Client).filter(Client.id == alert.client_id).first()
    asset = db.query(ClientAsset).filter(ClientAsset.id == alert.client_asset_id).first()
    return GeneratedAlertBrief(
        id=alert.id,
        client=client.name if client else None,
        asset=asset.name if asset else None,
        risk_level=alert.risk_level,
        status=alert.status,
    )


def _to_out(db: Session, alert: ClientAlert) -> AlertOut:
    """Attach friendly client/asset/event names for display."""
    client = db.query(Client).filter(Client.id == alert.client_id).first()
    asset = db.query(ClientAsset).filter(ClientAsset.id == alert.client_asset_id).first()
    event = db.query(Event).filter(Event.id == alert.event_id).first()
    out = AlertOut.model_validate(alert)
    out.client = client.name if client else None
    out.asset = asset.name if asset else None
    out.asset_type = asset.asset_type if asset else None
    out.event_title = event.title if event else None
    out.event_type = event.event_type if event else None
    return out
