KGP = {
    "code": "KGP",
    "name": "Komenda Główna Policji",
    "level": "kgp",
    "voivodeship": None,
}

KWP = [
    ("KWP-DŚ", "Komenda Wojewódzka Policji we Wrocławiu", "dolnoslaskie"),
    ("KWP-KP", "Komenda Wojewódzka Policji w Bydgoszczy", "kujawsko-pomorskie"),
    ("KWP-LU", "Komenda Wojewódzka Policji w Lublinie", "lubelskie"),
    ("KWP-LB", "Komenda Wojewódzka Policji w Gorzowie Wielkopolskim", "lubuskie"),
    ("KWP-ŁD", "Komenda Wojewódzka Policji w Łodzi", "lodzkie"),
    ("KWP-MP", "Komenda Wojewódzka Policji w Krakowie", "malopolskie"),
    ("KWP-MZ", "Komenda Wojewódzka Policji z siedzibą w Radomiu", "mazowieckie"),
    ("KSP-WA", "Komenda Stołeczna Policji", "mazowieckie"),
    ("KWP-OP", "Komenda Wojewódzka Policji w Opolu", "opolskie"),
    ("KWP-PK", "Komenda Wojewódzka Policji w Rzeszowie", "podkarpackie"),
    ("KWP-PD", "Komenda Wojewódzka Policji w Białymstoku", "podlaskie"),
    ("KWP-PM", "Komenda Wojewódzka Policji w Gdańsku", "pomorskie"),
    ("KWP-ŚL", "Komenda Wojewódzka Policji w Katowicach", "slaskie"),
    ("KWP-ŚK", "Komenda Wojewódzka Policji w Kielcach", "swietokrzyskie"),
    ("KWP-WM", "Komenda Wojewódzka Policji w Olsztynie", "warminsko-mazurskie"),
    ("KWP-WP", "Komenda Wojewódzka Policji w Poznaniu", "wielkopolskie"),
    ("KWP-ZP", "Komenda Wojewódzka Policji w Szczecinie", "zachodniopomorskie"),
]

VOIVODESHIPS = [
    ("dolnoslaskie", "dolnośląskie"),
    ("kujawsko-pomorskie", "kujawsko-pomorskie"),
    ("lubelskie", "lubelskie"),
    ("lubuskie", "lubuskie"),
    ("lodzkie", "łódzkie"),
    ("malopolskie", "małopolskie"),
    ("mazowieckie", "mazowieckie"),
    ("opolskie", "opolskie"),
    ("podkarpackie", "podkarpackie"),
    ("podlaskie", "podlaskie"),
    ("pomorskie", "pomorskie"),
    ("slaskie", "śląskie"),
    ("swietokrzyskie", "świętokrzyskie"),
    ("warminsko-mazurskie", "warmińsko-mazurskie"),
    ("wielkopolskie", "wielkopolskie"),
    ("zachodniopomorskie", "zachodniopomorskie"),
]


def structure():
    children = [
        {
            "code": code,
            "name": name,
            "level": "ksp" if code.startswith("KSP") else "kwp",
            "voivodeship": voi,
            "parent": "KGP",
        }
        for code, name, voi in KWP
    ]
    return {
        "kgp": KGP,
        "units": children,
        "login_units": all_units(),
        "voivodeships": [{"id": i, "label": l} for i, l in VOIVODESHIPS],
    }


def assign_unit(city: str | None, voivodeship: str | None) -> dict:
    city_l = (city or "").lower()
    voi = (voivodeship or "").lower()
    if "warszaw" in city_l or city_l.strip() in {"wawa", "warszawa"}:
        code, name, v = ("KSP-WA", "Komenda Stołeczna Policji", "mazowieckie")
        return {"code": code, "name": name, "voivodeship": v, "path": "KGP → KSP Warszawa"}
    for code, name, v in KWP:
        if v == voi and not code.startswith("KSP"):
            return {"code": code, "name": name, "voivodeship": v, "path": f"KGP → {name}"}
    return {
        "code": "KGP",
        "name": "Komenda Główna Policji",
        "voivodeship": voi or None,
        "path": "KGP (nie przypisano KWP — uzupełnij województwo)",
    }


def all_units():
    rows = [{"code": "KGP", "name": "Komenda Główna Policji", "level": "kgp"}]
    for code, name, voi in KWP:
        rows.append({"code": code, "name": name, "level": "ksp" if code.startswith("KSP") else "kwp", "voivodeship": voi})
    return rows


def valid_codes():
    return {u["code"] for u in all_units()}


def in_territory(unit_code: str, city: str | None, voivodeship: str | None) -> bool:
    if not unit_code or unit_code == "KGP":
        return True
    assigned = assign_unit(city, voivodeship)
    return assigned["code"] == unit_code
