from sqlalchemy.orm import Session

from app.models import Owner, Vehicle


def _owner(db, phone, **kwargs):
    row = db.query(Owner).filter(Owner.phone == phone).one_or_none()
    if row is None:
        row = Owner(phone=phone, **kwargs)
        db.add(row)
        db.flush()
        return row
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


def _vehicle(db, plate, owner_id, vin=None):
    row = db.query(Vehicle).filter(Vehicle.plate == plate).one_or_none()
    if row is None:
        db.add(Vehicle(plate=plate, vin=vin, owner_id=owner_id, is_active=True))
    else:
        row.owner_id = owner_id
        if vin:
            row.vin = vin


def seed_demo(db: Session) -> None:
    a = _owner(
        db,
        "696656585",
        first_name="Robert",
        last_name="Milewski",
        email="robert@example.pl",
        consent_contact=True,
        facebook="https://facebook.com/example.robert",
        x_handle="https://x.com/Pacanow",
        city="Warszawa",
        voivodeship="mazowieckie",
    )
    b = _owner(
        db,
        "555555555",
        first_name="Anna",
        last_name="Kowalczyk",
        consent_contact=False,
        city="Łódź",
        voivodeship="lodzkie",
    )
    c = _owner(
        db,
        "784139428",
        first_name="Tomasz",
        last_name="Mańkowski",
        consent_contact=True,
        facebook="https://facebook.com/tomek.mankowski",
        x_handle="https://x.com/tomaszmankowsk1",
        city="Ożarów Mazowiecki",
        voivodeship="mazowieckie",
    )
    db.flush()
    _vehicle(db, "WA00000", a.id, "VINWA00000ROBERT1")
    _vehicle(db, "WA11111", b.id, None)
    _vehicle(db, "WU3871", c.id, "SPALONYVIN3871XYZ")
    db.commit()
