"""Court database for Ukrainian judicial system.

Contains structured data about courts across Ukraine, including:
- Court names, addresses, jurisdictions
- Contact information
- Jurisdiction mapping by settlement/district/oblast
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass
class Court:
    """Representation of a single court."""

    id: str
    name: str
    court_type: str  # district, appeal, cassation, commercial, admin
    oblast: str
    district: str
    address: str
    phone: str = ""
    email: str = ""
    website: str = ""
    head_judge: str = ""
    jurisdiction_settlements: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


COURT_TYPES = {
    "district": "Районний суд",
    "city": "Міський суд",
    "city_district": "Районний суд у місті",
    "appeal": "Апеляційний суд",
    "cassation": "Касаційний суд",
    "commercial": "Господарський суд",
    "admin": "Окружний адміністративний суд",
    "appeal_commercial": "Апеляційний господарський суд",
    "appeal_admin": "Апеляційний адміністративний суд",
    "supreme": "Верховний Суд",
}

# Representative database of Ukrainian courts
COURTS_DB: List[Court] = [
    # --- Київська область ---
    Court(
        id="kyiv-shevchenk",
        name="Шевченківський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Володимирська, 15",
        phone="(044) 235-12-34",
        email="inbox@sh.kv.court.gov.ua",
        website="https://sh.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Шевченківський район)"],
    ),
    Court(
        id="kyiv-pechersk",
        name="Печерський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Хрещатик, 42-а",
        phone="(044) 253-45-67",
        email="inbox@pc.kv.court.gov.ua",
        website="https://pc.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Печерський район)"],
    ),
    Court(
        id="kyiv-darnytsk",
        name="Дарницький районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Кошиця, 5",
        phone="(044) 564-78-90",
        email="inbox@dr.kv.court.gov.ua",
        website="https://dr.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Дарницький район)"],
    ),
    Court(
        id="kyiv-desnyan",
        name="Деснянський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, просп. Маяковського, 3",
        phone="(044) 518-23-45",
        email="inbox@ds.kv.court.gov.ua",
        website="https://ds.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Деснянський район)"],
    ),
    Court(
        id="kyiv-golosiy",
        name="Голосіївський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, просп. Голосіївський, 23",
        phone="(044) 259-34-56",
        email="inbox@gl.kv.court.gov.ua",
        website="https://gl.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Голосіївський район)"],
    ),
    Court(
        id="kyiv-obolon",
        name="Оболонський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, просп. Оболонський, 32",
        phone="(044) 411-45-67",
        email="inbox@ob.kv.court.gov.ua",
        website="https://ob.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Оболонський район)"],
    ),
    Court(
        id="kyiv-podil",
        name="Подільський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Межигірська, 27",
        phone="(044) 425-56-78",
        email="inbox@pd.kv.court.gov.ua",
        website="https://pd.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Подільський район)"],
    ),
    Court(
        id="kyiv-solom",
        name="Солом'янський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Кудряшова, 4",
        phone="(044) 242-67-89",
        email="inbox@sl.kv.court.gov.ua",
        website="https://sl.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Солом'янський район)"],
    ),
    Court(
        id="kyiv-svyat",
        name="Святошинський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Жолудєва, 2а",
        phone="(044) 452-78-90",
        email="inbox@sv.kv.court.gov.ua",
        website="https://sv.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Святошинський район)"],
    ),
    Court(
        id="kyiv-dnipro",
        name="Дніпровський районний суд міста Києва",
        court_type="city_district",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Сержа Лифаря, 1",
        phone="(044) 292-89-01",
        email="inbox@dn.kv.court.gov.ua",
        website="https://dn.kv.court.gov.ua/",
        jurisdiction_settlements=["Київ (Дніпровський район)"],
    ),
    Court(
        id="bila-tserkva",
        name="Білоцерківський міськрайонний суд Київської області",
        court_type="city",
        oblast="Київська область",
        district="Білоцерківський район",
        address="м. Біла Церква, вул. Ярослава Мудрого, 33",
        phone="(04563) 5-12-34",
        email="inbox@bc.kv.court.gov.ua",
        website="https://bc.kv.court.gov.ua/",
        jurisdiction_settlements=[
            "Біла Церква", "Узин", "Ставище", "Рокитне", "Тетіїв",
        ],
    ),
    Court(
        id="boryspil",
        name="Бориспільський міськрайонний суд Київської області",
        court_type="city",
        oblast="Київська область",
        district="Бориспільський район",
        address="м. Бориспіль, вул. Головатого, 17",
        phone="(04595) 6-23-45",
        email="inbox@br.kv.court.gov.ua",
        website="https://br.kv.court.gov.ua/",
        jurisdiction_settlements=[
            "Бориспіль", "Переяслав", "Баришівка", "Березань",
        ],
    ),
    Court(
        id="irpin",
        name="Ірпінський міський суд Київської області",
        court_type="city",
        oblast="Київська область",
        district="Бучанський район",
        address="м. Ірпінь, вул. Шевченка, 2-а",
        phone="(04597) 3-34-56",
        email="inbox@ir.kv.court.gov.ua",
        website="https://ir.kv.court.gov.ua/",
        jurisdiction_settlements=["Ірпінь", "Буча", "Ворзель", "Гостомель"],
    ),
    # --- Львівська область ---
    Court(
        id="lviv-galytsk",
        name="Галицький районний суд міста Львова",
        court_type="city_district",
        oblast="Львівська область",
        district="м. Львів",
        address="м. Львів, вул. Князя Романа, 1",
        phone="(032) 261-12-34",
        email="inbox@gl.lv.court.gov.ua",
        website="https://gl.lv.court.gov.ua/",
        jurisdiction_settlements=["Львів (Галицький район)"],
    ),
    Court(
        id="lviv-lychakiv",
        name="Личаківський районний суд міста Львова",
        court_type="city_district",
        oblast="Львівська область",
        district="м. Львів",
        address="м. Львів, вул. Мечникова, 16",
        phone="(032) 276-23-45",
        email="inbox@lc.lv.court.gov.ua",
        website="https://lc.lv.court.gov.ua/",
        jurisdiction_settlements=["Львів (Личаківський район)"],
    ),
    Court(
        id="lviv-shevch",
        name="Шевченківський районний суд міста Львова",
        court_type="city_district",
        oblast="Львівська область",
        district="м. Львів",
        address="м. Львів, вул. Котляревського, 12",
        phone="(032) 233-34-56",
        email="inbox@sh.lv.court.gov.ua",
        website="https://sh.lv.court.gov.ua/",
        jurisdiction_settlements=["Львів (Шевченківський район)"],
    ),
    Court(
        id="drohobych",
        name="Дрогобицький міськрайонний суд Львівської області",
        court_type="city",
        oblast="Львівська область",
        district="Дрогобицький район",
        address="м. Дрогобич, вул. Грушевського, 2",
        phone="(03244) 2-45-67",
        email="inbox@dr.lv.court.gov.ua",
        website="https://dr.lv.court.gov.ua/",
        jurisdiction_settlements=["Дрогобич", "Трускавець", "Борислав", "Стебник"],
    ),
    # --- Одеська область ---
    Court(
        id="odesa-kyivsk",
        name="Київський районний суд м. Одеси",
        court_type="city_district",
        oblast="Одеська область",
        district="м. Одеса",
        address="м. Одеса, вул. Фонтанська дорога, 14",
        phone="(048) 723-12-34",
        email="inbox@kv.od.court.gov.ua",
        website="https://kv.od.court.gov.ua/",
        jurisdiction_settlements=["Одеса (Київський район)"],
    ),
    Court(
        id="odesa-primorsk",
        name="Приморський районний суд м. Одеси",
        court_type="city_district",
        oblast="Одеська область",
        district="м. Одеса",
        address="м. Одеса, вул. Черняховського, 12",
        phone="(048) 728-23-45",
        email="inbox@pr.od.court.gov.ua",
        website="https://pr.od.court.gov.ua/",
        jurisdiction_settlements=["Одеса (Приморський район)"],
    ),
    # --- Харківська область ---
    Court(
        id="kharkiv-dzerzhyn",
        name="Основ'янський районний суд м. Харкова",
        court_type="city_district",
        oblast="Харківська область",
        district="м. Харків",
        address="м. Харків, вул. Основ'янська, 4",
        phone="(057) 732-12-34",
        email="inbox@os.kh.court.gov.ua",
        website="https://os.kh.court.gov.ua/",
        jurisdiction_settlements=["Харків (Основ'янський район)"],
    ),
    Court(
        id="kharkiv-kyivsk",
        name="Київський районний суд м. Харкова",
        court_type="city_district",
        oblast="Харківська область",
        district="м. Харків",
        address="м. Харків, вул. Пушкінська, 5",
        phone="(057) 700-23-45",
        email="inbox@kv.kh.court.gov.ua",
        website="https://kv.kh.court.gov.ua/",
        jurisdiction_settlements=["Харків (Київський район)"],
    ),
    # --- Дніпропетровська область ---
    Court(
        id="dnipro-babushk",
        name="Бабушкінський районний суд м. Дніпропетровська",
        court_type="city_district",
        oblast="Дніпропетровська область",
        district="м. Дніпро",
        address="м. Дніпро, просп. Гагаріна, 73",
        phone="(056) 374-12-34",
        email="inbox@bb.dp.court.gov.ua",
        website="https://bb.dp.court.gov.ua/",
        jurisdiction_settlements=["Дніпро (Бабушкінський район)"],
    ),
    # --- Апеляційні суди ---
    Court(
        id="appeal-kyiv",
        name="Київський апеляційний суд",
        court_type="appeal",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Солом'янська, 2а",
        phone="(044) 205-50-00",
        email="inbox@kap.court.gov.ua",
        website="https://kap.court.gov.ua/",
        jurisdiction_settlements=[],
    ),
    Court(
        id="appeal-lviv",
        name="Львівський апеляційний суд",
        court_type="appeal",
        oblast="Львівська область",
        district="м. Львів",
        address="м. Львів, вул. Городоцька, 12",
        phone="(032) 235-60-00",
        email="inbox@lap.court.gov.ua",
        website="https://lap.court.gov.ua/",
        jurisdiction_settlements=[],
    ),
    # --- Господарські суди ---
    Court(
        id="commercial-kyiv",
        name="Господарський суд міста Києва",
        court_type="commercial",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, бул. Шевченка, 33/34",
        phone="(044) 235-10-00",
        email="inbox@gs.kv.court.gov.ua",
        website="https://gs.kv.court.gov.ua/",
        jurisdiction_settlements=[],
    ),
    Court(
        id="commercial-lviv",
        name="Господарський суд Львівської області",
        court_type="commercial",
        oblast="Львівська область",
        district="м. Львів",
        address="м. Львів, вул. Личаківська, 128",
        phone="(032) 275-10-00",
        email="inbox@gs.lv.court.gov.ua",
        website="https://gs.lv.court.gov.ua/",
        jurisdiction_settlements=[],
    ),
    # --- Адміністративні суди ---
    Court(
        id="admin-kyiv",
        name="Окружний адміністративний суд міста Києва",
        court_type="admin",
        oblast="Київська область",
        district="м. Київ",
        address="м. Київ, вул. Командарма Каменєва, 8",
        phone="(044) 364-20-00",
        email="inbox@oas.kv.court.gov.ua",
        website="https://oas.kv.court.gov.ua/",
        jurisdiction_settlements=[],
    ),
]


class CourtDatabase:
    """Searchable court database."""

    def __init__(self, courts: Optional[List[Court]] = None) -> None:
        self.courts = courts or COURTS_DB

    def search(
        self,
        query: str = "",
        oblast: str = "",
        court_type: str = "",
    ) -> List[Court]:
        """Search courts by query string, oblast and/or type."""
        results = self.courts
        if oblast:
            oblast_lower = oblast.lower()
            results = [c for c in results if oblast_lower in c.oblast.lower()]
        if court_type:
            results = [c for c in results if c.court_type == court_type]
        if query:
            q = query.lower()
            results = [
                c for c in results
                if q in c.name.lower()
                or q in c.address.lower()
                or q in c.district.lower()
                or any(q in s.lower() for s in c.jurisdiction_settlements)
            ]
        return results

    def find_by_settlement(self, settlement: str) -> List[Court]:
        """Find courts that have jurisdiction over a settlement."""
        s = settlement.lower()
        return [
            c for c in self.courts
            if any(s in js.lower() for js in c.jurisdiction_settlements)
            or s in c.district.lower()
            or s in c.name.lower()
        ]

    def find_by_id(self, court_id: str) -> Optional[Court]:
        """Find a court by its unique ID."""
        for c in self.courts:
            if c.id == court_id:
                return c
        return None

    def get_oblasts(self) -> List[str]:
        """Return sorted unique list of oblasts."""
        return sorted(set(c.oblast for c in self.courts))

    def get_types(self) -> List[str]:
        """Return sorted unique list of court types."""
        return sorted(set(c.court_type for c in self.courts))

    def stats(self) -> Dict[str, int]:
        """Return statistics about the database."""
        by_type: Dict[str, int] = {}
        for c in self.courts:
            label = COURT_TYPES.get(c.court_type, c.court_type)
            by_type[label] = by_type.get(label, 0) + 1
        return by_type

    def to_json(self) -> str:
        return json.dumps(
            [c.to_dict() for c in self.courts],
            ensure_ascii=False,
            indent=2,
        )
