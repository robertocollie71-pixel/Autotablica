from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.db import Base, SessionLocal, engine
from app.routers import admin, audit, auth, citizens, vehicles
from app.seed import seed_demo
from app.police_units import structure

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Warstwa cywilna – dobrowolny kontakt z właścicielem pojazdu",
)

origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(citizens.router)
app.include_router(vehicles.router)
app.include_router(audit.router)
app.include_router(admin.router)


def _migrate():
    cols = ("facebook", "instagram", "x_handle", "linkedin", "tiktok", "city", "voivodeship", "email")
    url = settings.DATABASE_URL
    with engine.begin() as conn:
        if url.startswith("sqlite"):
            existing = {row[1] for row in conn.execute(text("PRAGMA table_info(owners)"))}
            for name in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE owners ADD COLUMN {name} VARCHAR(200)"))
        else:
            existing = {
                row[0]
                for row in conn.execute(
                    text("SELECT column_name FROM information_schema.columns WHERE table_name = 'owners'")
                )
            }
            for name in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE owners ADD COLUMN {name} VARCHAR(200)"))


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    _migrate()
    db = SessionLocal()
    try:
        seed_demo(db)
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.APP_VERSION, "database": "postgres" if "postgres" in settings.DATABASE_URL else "sqlite"}


@app.get("/units")
def units():
    return structure()
