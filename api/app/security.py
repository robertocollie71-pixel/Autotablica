from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

bearer = HTTPBearer(auto_error=False)


def create_token(username: str, unit_code: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": username, "role": "officer", "unit": unit_code, "exp": exp}, settings.SECRET_KEY, algorithm="HS256")


def create_citizen_token(phone: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": phone, "role": "citizen", "exp": exp}, settings.SECRET_KEY, algorithm="HS256")


def _payload(creds):
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wymagane logowanie")
    try:
        return jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidłowy token")


def require_officer(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    payload = _payload(creds)
    if payload.get("role") and payload.get("role") != "officer":
        raise HTTPException(status_code=403, detail="To konto nie jest kontem służby")
    user = payload.get("sub")
    unit = payload.get("unit") or "KGP"
    if not user:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    return {"user": user, "unit": unit, "label": f"{user}@{unit}"}


def require_citizen(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    payload = _payload(creds)
    if payload.get("role") != "citizen":
        raise HTTPException(status_code=403, detail="Zaloguj się numerem telefonu jako obywatel")
    phone = payload.get("sub")
    if not phone:
        raise HTTPException(status_code=401, detail="Nieprawidłowy token")
    return phone
