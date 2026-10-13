from sqlalchemy.orm import Session

from app.models import AuditLog, Owner, Vehicle


def seed_demo(db: Session) -> None:
    db.query(AuditLog).delete()
    db.query(Vehicle).delete()
    db.query(Owner).delete()
    db.commit()