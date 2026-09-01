from io import BytesIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditLog
from app.security import require_officer

router = APIRouter(prefix="/audit", tags=["audit"])


def _rows(db: Session):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(2000).all()
    return [
        {
            "id": r.id,
            "actor": r.actor,
            "action": r.action,
            "plate": r.plate,
            "detail": r.detail,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("")
def list_audit(db: Session = Depends(get_db), officer: dict = Depends(require_officer)):
    return _rows(db)


@router.get(".xlsx")
def export_audit(db: Session = Depends(get_db), officer: dict = Depends(require_officer)):
    wb = Workbook()
    ws = wb.active
    ws.title = "Audyt"
    ws.append(["ID", "Czas", "Kto", "Akcja", "Tablica", "Wynik"])
    for r in _rows(db):
        ws.append([r["id"], r["created_at"], r["actor"], r["action"], r["plate"] or "", r["detail"] or ""])
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=mundurovehdb_audyt.xlsx"},
    )
