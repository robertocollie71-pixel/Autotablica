from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, Owner, Vehicle
from app.schemas import FleetItem, SocialOut, UnitOut, VehicleOut
from app.police_units import assign_unit, in_territory
from app.security import require_officer

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("/{query}", response_model=VehicleOut)
def lookup(query: str, db: Session = Depends(get_db), officer: dict = Depends(require_officer)):
    q = query.upper().replace(" ", "")
    digits = "".join(ch for ch in query if ch.isdigit())
    vehicle = (
        db.query(Vehicle)
        .filter((Vehicle.plate == q) | (Vehicle.vin == q), Vehicle.is_active.is_(True))
        .one_or_none()
    )
    if vehicle is None and len(digits) >= 9:
        owners = db.query(Owner).all()
        owner_hit = None
        for o in owners:
            ph = "".join(ch for ch in str(o.phone or "") if ch.isdigit())
            if ph.endswith(digits[-9:]) or digits.endswith(ph[-9:]):
                owner_hit = o
                break
        if owner_hit:
            vehicle = next((x for x in owner_hit.vehicles if x.is_active), None)

    if vehicle is None:
        db.add(AuditLog(actor=officer['label'], action="lookup", plate=q, detail="brak w rejestrze"))
        db.commit()
        raise HTTPException(status_code=404, detail="Brak pojazdu w rejestrze dobrowolnym")

    owner = vehicle.owner
    fleet = [
        FleetItem(plate=x.plate, vin=x.vin)
        for x in owner.vehicles
        if x.is_active
    ]

    if officer["unit"] != "KGP" and not in_territory(officer["unit"], owner.city, owner.voivodeship):
        assigned = assign_unit(owner.city, owner.voivodeship)
        db.add(AuditLog(actor=officer["label"], action="lookup", plate=vehicle.plate, detail="poza terenem"))
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Obywatel przypisany do innej komendy: " + assigned["path"] + ". Zaloguj się na KGP albo właściwą jednostkę.",
        )

    if not owner.consent_contact:
        db.add(AuditLog(actor=officer['label'], action="lookup", plate=vehicle.plate, detail="brak zgody"))
        db.commit()
        return VehicleOut(
            plate=vehicle.plate,
            vin=vehicle.vin,
            owner_name="Ukryte — brak zgody na kontakt",
            phone=None,
            email=None,
            consent_contact=False,
            social=SocialOut(),
            city=None,
            voivodeship=None,
            unit=None,
            vehicles=[],
            message="Właściciel nie wyraził zgody na kontakt. Nie pokazujemy telefonu, profili ani pozostałych pojazdów.",
        )

    db.add(AuditLog(actor=officer['label'], action="lookup", plate=vehicle.plate, detail="kontakt udostępniony"))
    db.commit()
    return VehicleOut(
        plate=vehicle.plate,
        vin=vehicle.vin,
        owner_name=f"{owner.first_name} {owner.last_name}",
        phone=owner.phone,
        email=owner.email,
        consent_contact=True,
        social=SocialOut(
            facebook=owner.facebook,
            instagram=owner.instagram,
            x_handle=owner.x_handle,
            linkedin=owner.linkedin,
            tiktok=owner.tiktok,
        ),
        city=owner.city,
        voivodeship=owner.voivodeship,
        unit=UnitOut(**assign_unit(owner.city, owner.voivodeship)),
        vehicles=fleet,
        message="Właściciel wyraził zgodę na kontakt służbowy.",
    )
