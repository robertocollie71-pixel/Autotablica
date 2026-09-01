from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Owner
from app.police_units import assign_unit, in_territory
from app.security import require_officer

router = APIRouter(prefix="/admin", tags=["admin"])


def _rows(db: Session, unit_code: str):
    owners = db.query(Owner).order_by(Owner.id.asc()).all()
    out = []
    for o in owners:
        if unit_code != "KGP" and not in_territory(unit_code, o.city, o.voivodeship):
            continue
        plates = [v.plate for v in o.vehicles if v.is_active]
        vins = [v.vin for v in o.vehicles if v.is_active and v.vin]
        assigned = assign_unit(o.city, o.voivodeship)
        out.append(
            {
                "id": o.id,
                "first_name": o.first_name,
                "last_name": o.last_name,
                "phone": o.phone,
                "email": o.email or "",
                "consent_contact": bool(o.consent_contact),
                "vehicles": plates,
                "vins": vins,
                "facebook": o.facebook or "",
                "instagram": o.instagram or "",
                "x_handle": o.x_handle or "",
                "linkedin": o.linkedin or "",
                "tiktok": o.tiktok or "",
                "city": o.city or "",
                "voivodeship": o.voivodeship or "",
                "unit": assigned["name"],
                "unit_code": assigned["code"],
            }
        )
    return out


def _filter_units(rows, units: str | None):
    if not units:
        return rows
    codes = {c.strip() for c in units.split(",") if c.strip()}
    if not codes:
        return rows
    return [r for r in rows if r.get("unit_code") in codes]


@router.get("/citizens")
def list_citizens(db: Session = Depends(get_db), officer: dict = Depends(require_officer)):
    return _rows(db, officer["unit"])


@router.get("/citizens.xlsx")
def export_xlsx(
    db: Session = Depends(get_db),
    officer: dict = Depends(require_officer),
    units: str | None = Query(None),
):
    wb = Workbook()
    ws = wb.active
    ws.title = "Obywatele"
    ws.append(
        [
            "ID", "Imię", "Nazwisko", "Telefon", "E-mail", "Zgoda na kontakt",
            "Pojazdy", "VIN", "Miejscowość", "Województwo", "Komenda",
            "Facebook", "Instagram", "X", "LinkedIn", "TikTok",
        ]
    )
    for r in _filter_units(_rows(db, officer["unit"]), units):
        ws.append(
            [
                r["id"], r["first_name"], r["last_name"], r["phone"], r.get("email",""),
                "tak" if r["consent_contact"] else "nie",
                ", ".join(r["vehicles"]), ", ".join(r["vins"]),
                r["city"], r["voivodeship"], r["unit"],
                r["facebook"], r["instagram"], r["x_handle"], r["linkedin"], r.get("tiktok",""),
            ]
        )
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=mundurovehdb_obywatele.xlsx"},
    )
