from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    username: str
    password: str
    unit_code: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    unit_code: str
    unit_name: str


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=9, max_length=32)
    email: str | None = None
    plate: str = Field(min_length=3, max_length=16)
    vin: str | None = Field(default=None, max_length=32)
    facebook: str | None = None
    instagram: str | None = None
    x_handle: str | None = None
    linkedin: str | None = None
    tiktok: str | None = None
    city: str | None = None
    voivodeship: str | None = None
    consent_contact: bool


class SocialOut(BaseModel):
    facebook: str | None = None
    instagram: str | None = None
    x_handle: str | None = None
    linkedin: str | None = None
    tiktok: str | None = None


class FleetItem(BaseModel):
    plate: str
    vin: str | None = None


class UnitOut(BaseModel):
    code: str
    name: str
    voivodeship: str | None = None
    path: str


class VehicleOut(BaseModel):
    plate: str
    vin: str | None
    owner_name: str
    phone: str | None
    email: str | None = None
    city: str | None = None
    voivodeship: str | None = None
    unit: UnitOut | None = None
    consent_contact: bool
    social: SocialOut
    vehicles: list[FleetItem] = []
    message: str
