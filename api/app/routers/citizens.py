from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog, Owner, Vehicle
from app.schemas import RegisterIn
from app.security import create_citizen_token, require_citizen

router = APIRouter(prefix="/citizens", tags=["citizens"])


class PhoneIn(BaseModel):
    phone: str


def _clean(url):
    if not url:
        return None
    url = str(url).strip()
    return url or None


def _digits(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def _pack(owner: Owner):
    return {
        "first_name": owner.first_name,
        "last_name": owner.last_name,
        "phone": owner.phone,
        "email": owner.email,
        "city": owner.city,
        "voivodeship": owner.voivodeship,
        "consent_contact": bool(owner.consent_contact),
        "facebook": owner.facebook,
        "instagram": owner.instagram,
        "x_handle": owner.x_handle,
        "linkedin": owner.linkedin,
        "tiktok": owner.tiktok,
        "vehicles": [
            {"plate": v.plate, "vin": v.vin}
            for v in owner.vehicles
            if v.is_active
        ],
        "access_token": None,
    }


@router.post("/login")
def login(body: PhoneIn, db: Session = Depends(get_db)):
    phone = _digits(body.phone)
    owner = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail="Brak profilu dla tego numeru. Zarejestruj się.")
    db.add(AuditLog(actor=phone, action="citizen_login", plate=None, detail="logowanie obywatela"))
    db.commit()
    data = _pack(owner)
    data["access_token"] = create_citizen_token(phone)
    data["message"] = "Zalogowano."
    return data


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if not body.consent_contact:
        raise HTTPException(status_code=400, detail="Wymagana zgoda na kontakt służbowy")

    plate = body.plate.upper().replace(" ", "")
    vin = body.vin.upper().replace(" ", "") if body.vin else None
    phone = _digits(body.phone)

    owner = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    created = owner is None
    if owner is None:
        owner = Owner(
            first_name=body.first_name.strip(),
            last_name=body.last_name.strip(),
            phone=phone,
            email=_clean(body.email),
            consent_contact=True,
            facebook=_clean(body.facebook),
            instagram=_clean(body.instagram),
            x_handle=_clean(body.x_handle),
            linkedin=_clean(body.linkedin),
            tiktok=_clean(body.tiktok),
            city=_clean(body.city),
            voivodeship=_clean(body.voivodeship),
        )
        db.add(owner)
        db.flush()
    else:
        owner.first_name = body.first_name.strip()
        owner.last_name = body.last_name.strip()
        owner.consent_contact = True
        owner.email = _clean(body.email)
        owner.facebook = _clean(body.facebook)
        owner.instagram = _clean(body.instagram)
        owner.x_handle = _clean(body.x_handle)
        owner.linkedin = _clean(body.linkedin)
        owner.tiktok = _clean(body.tiktok)
        owner.city = _clean(body.city)
        owner.voivodeship = _clean(body.voivodeship)

    existing = db.query(Vehicle).filter(Vehicle.plate == plate).one_or_none()
    if existing and existing.owner_id != owner.id:
        raise HTTPException(status_code=409, detail="Ten numer rejestracyjny jest już przypisany do innego właściciela")
    if existing is None:
        db.add(Vehicle(plate=plate, vin=vin, owner_id=owner.id, is_active=True))
    else:
        existing.vin = vin or existing.vin
        existing.is_active = True

    db.add(AuditLog(actor=phone, action="register_vehicle", plate=plate, detail="nowy profil" if created else "dopisano pojazd"))
    db.commit()
    data = _pack(owner)
    data["access_token"] = create_citizen_token(phone)
    data["message"] = "Profil zapisany. Jesteś zalogowany."
    return data


@router.get("/me")
def me(phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail="Profil usunięty")
    return _pack(owner)


@router.put("/me")
def update_me(body: RegisterIn, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail="Brak profilu")
    owner.first_name = body.first_name.strip()
    owner.last_name = body.last_name.strip()
    owner.email = _clean(body.email)
    owner.city = _clean(body.city)
    owner.voivodeship = _clean(body.voivodeship)
    owner.facebook = _clean(body.facebook)
    owner.instagram = _clean(body.instagram)
    owner.x_handle = _clean(body.x_handle)
    owner.linkedin = _clean(body.linkedin)
    owner.tiktok = _clean(body.tiktok)
    owner.consent_contact = bool(body.consent_contact)
    if body.plate:
        plate = body.plate.upper().replace(" ", "")
        vin = body.vin.upper().replace(" ", "") if body.vin else None
        existing = db.query(Vehicle).filter(Vehicle.plate == plate).one_or_none()
        if existing and existing.owner_id != owner.id:
            raise HTTPException(status_code=409, detail="Tablica należy do innego właściciela")
        if existing is None:
            db.add(Vehicle(plate=plate, vin=vin, owner_id=owner.id, is_active=True))
        elif vin:
            existing.vin = vin
    db.add(AuditLog(actor=phone, action="update_profile", plate=body.plate, detail="obywatel zmienił dane"))
    db.commit()
    data = _pack(owner)
    data["message"] = "Dane zaktualizowane. Zmiana widoczna w audycie służby."
    return data


@router.delete("/me")
def delete_me(phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail="Brak profilu")
    for v in list(owner.vehicles):
        v.is_active = False
    owner.consent_contact = False
    db.add(AuditLog(actor=phone, action="delete_profile", plate=None, detail="obywatel wycofał zgodę i ukrył pojazdy"))
    db.commit()
    return {"status": "ok", "message": "Profil wyłączony. Służba nie zobaczy kontaktu."}


class VehicleIn(BaseModel):
    plate: str
    vin: str | None = None


class ProfileIn(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    city: str | None = None
    voivodeship: str | None = None


class SocialIn(BaseModel):
    facebook: str | None = None
    instagram: str | None = None
    x_handle: str | None = None
    linkedin: str | None = None
    tiktok: str | None = None


def _owner(db, phone):
    owner = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    if owner is None:
        raise HTTPException(status_code=404, detail="Brak profilu")
    return owner


@router.post("/me/vehicles")
def add_vehicle(body: VehicleIn, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = _owner(db, phone)
    plate = body.plate.upper().replace(" ", "")
    vin = body.vin.upper().replace(" ", "") if body.vin else None
    existing = db.query(Vehicle).filter(Vehicle.plate == plate).one_or_none()
    if existing and existing.owner_id != owner.id:
        raise HTTPException(status_code=409, detail="Tablica należy do innego właściciela")
    if existing is None:
        db.add(Vehicle(plate=plate, vin=vin, owner_id=owner.id, is_active=True))
    else:
        existing.is_active = True
        if vin:
            existing.vin = vin
    db.add(AuditLog(actor=phone, action="add_vehicle", plate=plate, detail="obywatel dodał pojazd"))
    db.commit()
    return _pack(owner)


@router.delete("/me/vehicles/{plate}")
def remove_vehicle(plate: str, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = _owner(db, phone)
    p = plate.upper().replace(" ", "")
    row = db.query(Vehicle).filter(Vehicle.plate == p, Vehicle.owner_id == owner.id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Brak pojazdu")
    row.is_active = False
    db.add(AuditLog(actor=phone, action="delete_vehicle", plate=p, detail="obywatel usunął pojazd"))
    db.commit()
    return _pack(owner)


@router.put("/me/social")
def update_social(body: SocialIn, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = _owner(db, phone)
    owner.facebook = _clean(body.facebook) if body.facebook is not None else owner.facebook
    owner.instagram = _clean(body.instagram) if body.instagram is not None else owner.instagram
    owner.x_handle = _clean(body.x_handle) if body.x_handle is not None else owner.x_handle
    owner.linkedin = _clean(body.linkedin) if body.linkedin is not None else owner.linkedin
    owner.tiktok = _clean(body.tiktok) if body.tiktok is not None else owner.tiktok
    db.add(AuditLog(actor=phone, action="update_social", plate=None, detail="obywatel zmienił social media"))
    db.commit()
    return _pack(owner)


@router.delete("/me/social/{field}")
def delete_social(field: str, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = _owner(db, phone)
    allowed = {"facebook", "instagram", "x_handle", "linkedin", "tiktok"}
    if field not in allowed:
        raise HTTPException(status_code=400, detail="Nieznany kanał")
    setattr(owner, field, None)
    db.add(AuditLog(actor=phone, action="delete_social", plate=None, detail="usunięto " + field))
    db.commit()
    return _pack(owner)


@router.put("/me/profile")
def update_profile(body: ProfileIn, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = _owner(db, phone)
    new_phone = "".join(ch for ch in body.phone if ch.isdigit())
    if new_phone != owner.phone:
        clash = db.query(Owner).filter(Owner.phone == new_phone, Owner.id != owner.id).one_or_none()
        if clash:
            raise HTTPException(status_code=409, detail="Ten numer telefonu jest już w rejestrze")
        db.add(AuditLog(actor=phone, action="update_phone", plate=None, detail="stary " + owner.phone + " → " + new_phone))
        owner.phone = new_phone
        phone = new_phone
    owner.first_name = body.first_name.strip()
    owner.last_name = body.last_name.strip()
    owner.email = _clean(body.email)
    owner.city = _clean(body.city)
    owner.voivodeship = _clean(body.voivodeship)
    db.add(AuditLog(actor=phone, action="update_profile", plate=None, detail="obywatel zmienił dane osobowe / lokalizację"))
    db.commit()
    data = _pack(owner)
    data["access_token"] = create_citizen_token(owner.phone)
    data["message"] = "Profil zaktualizowany."
    return data


@router.put("/me/vehicles/{plate}")
def edit_vehicle(plate: str, body: VehicleIn, phone: str = Depends(require_citizen), db: Session = Depends(get_db)):
    owner = _owner(db, phone)
    old = plate.upper().replace(" ", "")
    row = db.query(Vehicle).filter(Vehicle.plate == old, Vehicle.owner_id == owner.id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Brak pojazdu")
    new_plate = body.plate.upper().replace(" ", "")
    vin = body.vin.upper().replace(" ", "") if body.vin else None
    if new_plate != old:
        clash = db.query(Vehicle).filter(Vehicle.plate == new_plate).one_or_none()
        if clash and clash.id != row.id:
            raise HTTPException(status_code=409, detail="Taka tablica już istnieje")
        db.add(AuditLog(actor=phone, action="update_vehicle", plate=new_plate, detail="tablica " + old + " → " + new_plate))
        row.plate = new_plate
    if vin is not None:
        row.vin = vin or None
        db.add(AuditLog(actor=phone, action="update_vehicle", plate=row.plate, detail="zmiana VIN"))
    db.commit()
    return _pack(owner)
