from fastapi import APIRouter, HTTPException

from app.config import settings
from app.police_units import all_units, valid_codes
from app.schemas import LoginIn, TokenOut
from app.security import create_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn):
    if body.username != settings.OFFICER_USER or body.password != settings.OFFICER_PASSWORD:
        raise HTTPException(status_code=401, detail="Błędny login lub hasło")
    code = (body.unit_code or "").strip()
    if code not in valid_codes():
        raise HTTPException(status_code=400, detail="Wybierz komendę z listy")
    names = {u["code"]: u["name"] for u in all_units()}
    return TokenOut(access_token=create_token(body.username, code), unit_code=code, unit_name=names[code])
