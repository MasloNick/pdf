"""Scrapers for individual bank websites and private auction platforms.

Each bank may publish NPL portfolio sale announcements on their own website
in different formats.  This module provides per-bank scrapers and a registry
that runs them all.

IMPORTANT: Only URLs that are known to be real are stored with
``url_verified=True``.  All other URLs need manual verification before
relying on them — the scraper will still attempt to fetch them, but the
UI marks them accordingly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from scripts.scrapers.base import BaseScraper, extract_links

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bank / MFO / FC registry
# ---------------------------------------------------------------------------

@dataclass
class BankConfig:
    """Configuration for scraping a specific bank/MFO/FC."""
    name: str
    short_name: str
    bank_type: str                  # state_bank / private_bank / mfo / fc
    website: str
    url_verified: bool = False      # True = URL вручну перевірено і веде куди треба
    npl_page: Optional[str] = None  # пряме посилання на сторінку продажу NPL
    npl_page_verified: bool = False
    accreditation_page: Optional[str] = None
    news_page: Optional[str] = None
    keywords: List[str] = field(default_factory=lambda: [
        "право вимоги", "портфель", "кредитний портфель",
        "продаж", "аукціон", "торги", "реалізація",
        "непрацюючі активи", "дебіторська",
    ])
    notes: str = ""


# ---------------------------------------------------------------------------
# REGISTRY — банки, МФО, ФК
#
# url_verified=True означає що домен точно належить цій організації.
# npl_page_verified=True означає що URL безпосередньо веде на сторінку
# продажу активів / NPL і був перевірений.
# Якщо verified=False — скрапер все одно спробує, але в UI буде мітка.
# ---------------------------------------------------------------------------

BANK_REGISTRY: List[BankConfig] = [

    # === ДЕРЖАВНІ БАНКИ ===

    BankConfig(
        name="АТ КБ «ПриватБанк»",
        short_name="ПриватБанк",
        bank_type="state_bank",
        website="https://privatbank.ua",
        url_verified=True,
        # Сторінка продажу активів ПриватБанку — потрібно перевірити актуальний шлях
        npl_page=None,
        news_page=None,
        notes="Найбільший банк України. Регулярно продає NPL-портфелі через ProZorro.Sale. "
              "Також має внутрішні тендери. Шукати на ProZorro за назвою продавця.",
    ),
    BankConfig(
        name="АТ «Ощадбанк»",
        short_name="Ощадбанк",
        bank_type="state_bank",
        website="https://oschadbank.ua",
        url_verified=True,
        notes="Державний. Продає через ProZorro.Sale.",
    ),
    BankConfig(
        name="АТ «Укрексімбанк»",
        short_name="Укрексімбанк",
        bank_type="state_bank",
        website="https://eximb.com",
        url_verified=True,
        notes="Державний. Продає через ProZorro.Sale та внутрішні тендери.",
    ),
    BankConfig(
        name="АБ «Укргазбанк»",
        short_name="Укргазбанк",
        bank_type="state_bank",
        website="https://ukrgasbank.com",
        url_verified=True,
        notes="Державний.",
    ),

    # === ПРИВАТНІ БАНКИ ===

    BankConfig(
        name="АТ «ПУМБ»",
        short_name="ПУМБ",
        bank_type="private_bank",
        website="https://pumb.ua",
        url_verified=True,
        notes="Один з найбільших приватних банків. Проводить тендери серед ФК.",
    ),
    BankConfig(
        name="АТ «Сенс Банк» (колишній Альфа-Банк)",
        short_name="Сенс Банк",
        bank_type="private_bank",
        website="https://sensbank.com.ua",
        url_verified=True,
        notes="Колишній Альфа-Банк Україна, ребрендинг 2022.",
    ),
    BankConfig(
        name="АТ «Креді Агріколь Банк»",
        short_name="Креді Агріколь",
        bank_type="private_bank",
        website="https://credit-agricole.ua",
        url_verified=True,
        notes="Проводить внутрішні закриті аукціони серед акредитованих ФК. "
              "Для акредитації: ліцензія ФК, досвід NPL, заявка через відділ проблемних активів банку.",
    ),
    BankConfig(
        name="АТ «Райффайзен Банк»",
        short_name="Райффайзен",
        bank_type="private_bank",
        website="https://raiffeisen.ua",
        url_verified=True,
        notes="Міжнародний банк, може проводити продажі NPL через материнську групу.",
    ),
    BankConfig(
        name="АТ «ОТП Банк»",
        short_name="ОТП Банк",
        bank_type="private_bank",
        website="https://otpbank.com.ua",
        url_verified=True,
        notes="Частина OTP Group (Угорщина).",
    ),
    BankConfig(
        name="АТ «Укрсиббанк»",
        short_name="Укрсиббанк",
        bank_type="private_bank",
        website="https://ukrsibbank.com",
        url_verified=True,
        notes="Частина BNP Paribas Group.",
    ),
    BankConfig(
        name="АТ «Універсал Банк» (monobank)",
        short_name="Універсал Банк",
        bank_type="private_bank",
        website="https://universalbank.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «А-Банк»",
        short_name="А-Банк",
        bank_type="private_bank",
        website="https://a-bank.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Прокредит Банк»",
        short_name="Прокредит",
        bank_type="private_bank",
        website="https://procreditbank.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Банк Кредит Дніпро»",
        short_name="Кредит Дніпро",
        bank_type="private_bank",
        website="https://creditdnepr.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Таскомбанк»",
        short_name="Таскомбанк",
        bank_type="private_bank",
        website="https://tascombank.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Правекс Банк»",
        short_name="Правекс",
        bank_type="private_bank",
        website="https://pravex.com.ua",
        url_verified=True,
        notes="Належить Intesa Sanpaolo (Італія).",
    ),
    BankConfig(
        name="АТ «Кредобанк»",
        short_name="Кредобанк",
        bank_type="private_bank",
        website="https://kredobank.com.ua",
        url_verified=True,
        notes="Належить PKO BP (Польща).",
    ),
    BankConfig(
        name="АТ «Банк Восток»",
        short_name="Банк Восток",
        bank_type="private_bank",
        website="https://bankvostok.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Мегабанк»",
        short_name="Мегабанк",
        bank_type="private_bank",
        website="https://megabank.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Банк Форвард»",
        short_name="Форвард",
        bank_type="private_bank",
        website="https://forward-bank.com",
        url_verified=True,
        notes="Спеціалізується на споживчому кредитуванні, може мати NPL-портфелі.",
    ),
    BankConfig(
        name="АТ «Ідея Банк»",
        short_name="Ідея Банк",
        bank_type="private_bank",
        website="https://ideabank.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «МТБ Банк»",
        short_name="МТБ Банк",
        bank_type="private_bank",
        website="https://mtb.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Банк Альянс»",
        short_name="Банк Альянс",
        bank_type="private_bank",
        website="https://bankalliance.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Глобус Банк»",
        short_name="Глобус Банк",
        bank_type="private_bank",
        website="https://globusbank.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Акордбанк»",
        short_name="Акордбанк",
        bank_type="private_bank",
        website="https://accordbank.com.ua",
        url_verified=True,
    ),
    # Банк Січ — ліквідований НБУ 06.10.2022, перенесений до DGF_LIQUIDATED_BANKS
    BankConfig(
        name="АТ «Полікомбанк»",
        short_name="Полікомбанк",
        bank_type="private_bank",
        website="https://polikombank.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «КІБ» (Комерційний Індустріальний Банк)",
        short_name="КІБ",
        bank_type="private_bank",
        website="https://cib.com.ua",
        url_verified=True,
    ),
    BankConfig(
        name="АТ «Піреус Банк»",
        short_name="Піреус Банк",
        bank_type="private_bank",
        website="https://piraeusbank.ua",
        url_verified=True,
        notes="Належить грецькій Piraeus Bank Group.",
    ),

    # === МФО (мікрофінансові організації) ===
    # Великі МФО мають значні портфелі мікрокредитів, які можуть продавати
    # на закритих торгах. Інформацію шукати у їхній фінзвітності на
    # stockmarket.gov.ua та в рішеннях АМКУ.

    BankConfig(
        name="ТОВ «Манівео»",
        short_name="Манівео",
        bank_type="mfo",
        website="https://moneyveo.ua",
        url_verified=True,
        notes="Одна з найбільших МФО України. Може продавати портфелі на закритих торгах. "
              "Перевіряти фінзвітність на stockmarket.gov.ua.",
    ),
    BankConfig(
        name="ТОВ «MyCredit»",
        short_name="MyCredit",
        bank_type="mfo",
        website="https://mycredit.ua",
        url_verified=True,
        notes="Велика МФО. Шукати згадки продажу портфелів у квартальних звітах.",
    ),
    # CCloan — ліцензія відкликана НБУ, компанія не працює
    BankConfig(
        name="ТОВ «КредитМаркет»",
        short_name="КредитМаркет",
        bank_type="mfo",
        website="https://creditmarket.ua",
        url_verified=True,
    ),
    # Dinero — ліцензія відкликана НБУ 01.12.2020, компанія не працює
    BankConfig(
        name="ТОВ «Aventus» (Швидко Гроші)",
        short_name="Aventus",
        bank_type="mfo",
        website="https://shvidko-groshi.com.ua",
        url_verified=True,
        notes="Група Aventus — одна з найбільших МФО-груп в Україні.",
    ),
    BankConfig(
        name="ТОВ «Credit Plus»",
        short_name="Credit Plus",
        bank_type="mfo",
        website="https://creditplus.ua",
        url_verified=True,
    ),
    BankConfig(
        name="ТОВ «ТерГроші» (Tergroshy)",
        short_name="ТерГроші",
        bank_type="mfo",
        website="https://tergroshy.com.ua",
        url_verified=False,
    ),
    BankConfig(
        name="ТОВ «Позичай»",
        short_name="Позичай",
        bank_type="mfo",
        website="https://pozychay.com.ua",
        url_verified=False,
    ),

    # === ФК (фінансові компанії — колектори / факторинг) ===
    # Великі ФК — це і покупці NPL-портфелів, і потенційні продавці
    # (перепродаж частин портфеля). Відстежувати через:
    # 1) Рішення АМКУ про концентрацію
    # 2) Масові позови в реєстрі судових рішень (reyestr.court.gov.ua)
    # 3) Фінзвітність на stockmarket.gov.ua

    BankConfig(
        name="ТОВ «ФК Форінт»",
        short_name="Форінт",
        bank_type="fc",
        website="https://forint.com.ua",
        url_verified=False,
        notes="Одна з найбільших ФК-колекторів України. Може перепродавати частини портфелів.",
    ),
    BankConfig(
        name="ТОВ «Вердикт»",
        short_name="Вердикт",
        bank_type="fc",
        website="https://verdykt.com.ua",
        url_verified=False,
    ),
    BankConfig(
        name="ТОВ «ФК Укрборг»",
        short_name="Укрборг",
        bank_type="fc",
        website="https://ukrborg.ua",
        url_verified=False,
        notes="Велика ФК, активний покупець портфелів ПриватБанку та ФГВ. "
              "Перевірити через ЄДРПОУ в судовому реєстрі — масові позови = активна робота з NPL.",
    ),
    BankConfig(
        name="ТОВ «ФК Кредекс»",
        short_name="Кредекс",
        bank_type="fc",
        website="https://credex.com.ua",
        url_verified=False,
    ),
    BankConfig(
        name="ТОВ «ФК Фактор Плюс»",
        short_name="Фактор Плюс",
        bank_type="fc",
        website="https://factorplus.com.ua",
        url_verified=False,
        notes="Факторингова компанія, спеціалізується на викупі дебіторки.",
    ),
]


# ---------------------------------------------------------------------------
# Торгові платформи та джерела пошуку
# ---------------------------------------------------------------------------

AUCTION_PLATFORMS = [
    {
        "name": "SETAM — Система електронних торгів арештованим майном",
        "url": "https://setam.net.ua",
        "search_url": "https://setam.net.ua/auctions",
        "description": "ДП СЕТАМ — офіційна платформа для продажу арештованого та конфіскованого майна, "
                       "включаючи портфелі прав вимоги.",
        "type": "state",
        "verified": True,
        "how_to_search": "На сторінці пошуку ввести 'право вимоги' або 'портфель кредитів'.",
    },
    {
        "name": "ProZorro.Продажі",
        "url": "https://prozorro.sale",
        "search_url": "https://prozorro.sale/auction/search?query=%D0%BF%D1%80%D0%B0%D0%B2%D0%BE+%D0%B2%D0%B8%D0%BC%D0%BE%D0%B3%D0%B8",
        "description": "Єдина державна платформа для продажу активів. Всі державні банки та ФГВ "
                       "зобов'язані продавати через неї.",
        "type": "state",
        "verified": True,
        "how_to_search": "Пошук за фразами 'право вимоги', 'кредитний портфель', 'непрацюючі активи'. "
                         "Фільтр по організатору = назва банку.",
    },
    {
        "name": "ФГВ — Фонд гарантування вкладів фізичних осіб",
        "url": "https://www.fg.gov.ua",
        "search_url": "https://www.fg.gov.ua/news",
        "description": "Продає активи ліквідованих банків (ПриватБанк old, Дельта, Надра, Фінансова Ініціатива тощо). "
                       "Основний канал продажу — ProZorro.Sale, але оголошення публікуються на сайті ФГВ.",
        "type": "state",
        "verified": True,
        "how_to_search": "Розділ новин — шукати 'реалізація активів', 'право вимоги'. "
                         "Також розділ 'Управління активами'.",
    },
    {
        "name": "НБУ — Національний банк України (статистика NPL)",
        "url": "https://bank.gov.ua",
        "search_url": "https://bank.gov.ua/ua/statistic/supervision-statist",
        "description": "Статистика NPL по банківській системі. Не продає портфелі, але дані про рівень NPL "
                       "допомагають зрозуміти які банки мають великі обсяги проблемних активів.",
        "type": "analytics",
        "verified": True,
        "how_to_search": "Розділ 'Банківський нагляд' → 'Статистична інформація'. "
                         "Звіти про фінансовий стан банків показують NPL ratios.",
    },
    {
        "name": "НКЦПФР — Національна комісія з цінних паперів",
        "url": "https://www.nssmc.gov.ua",
        "search_url": "https://stockmarket.gov.ua",
        "description": "Реєстр фінансових компаній та їх звітність. ФК зобов'язані розкривати інформацію "
                       "про суттєві транзакції, включаючи купівлю/продаж портфелів прав вимоги.",
        "type": "analytics",
        "verified": True,
        "how_to_search": "stockmarket.gov.ua — Розкриття інформації емітентами. Шукати звіти ФК "
                         "з ключовими словами 'відступлення прав вимоги', 'портфель'.",
    },
    {
        "name": "Єдиний реєстр судових рішень",
        "url": "https://reyestr.court.gov.ua",
        "search_url": "https://reyestr.court.gov.ua",
        "description": "Пошук судових рішень. Масові позови від однієї ФК = вони купили портфель. "
                       "Також пошук рішень про відступлення прав вимоги.",
        "type": "analytics",
        "verified": True,
        "how_to_search": "Пошук за текстом 'відступлення права вимоги' + назва банку/ФК. "
                         "Або за позивачем = назва ФК → побачити по яких кредитах судяться.",
    },
    {
        "name": "АМКУ — Антимонопольний комітет України",
        "url": "https://amcu.gov.ua",
        "search_url": "https://amcu.gov.ua/napryami/konkurentne-zakonodavstvo/kontsentratsiyi",
        "description": "Великі угоди з купівлі NPL-портфелів потребують дозволу АМКУ на концентрацію. "
                       "Публічні рішення АМКУ розкривають хто, у кого і за скільки купив.",
        "type": "analytics",
        "verified": True,
        "how_to_search": "Розділ 'Концентрації' — шукати рішення що стосуються фінансових компаній "
                         "та відступлення прав вимоги.",
    },
    {
        "name": "OpenDataBot",
        "url": "https://opendatabot.ua",
        "search_url": "https://opendatabot.ua",
        "description": "Агрегатор відкритих даних. Перевірка компаній, судових справ, виконавчих проваджень. "
                       "Корисно для перевірки покупців портфелів та юросіб-боржників.",
        "type": "analytics",
        "verified": True,
        "how_to_search": "Ввести код ЄДРПОУ або назву компанії.",
    },
    {
        "name": "Закриті банківські тендери",
        "url": "",
        "search_url": "",
        "description": "Креді Агріколь, ПУМБ, Райффайзен та інші проводять внутрішні аукціони серед акредитованих ФК. "
                       "Інформація не публікується відкрито — потрібна акредитація та прямий контакт з банком.",
        "type": "closed",
        "verified": True,
        "how_to_search": "Зв'язатися з відділом проблемних активів / workout department банку. "
                         "Подати заявку на акредитацію як ФК.",
    },
]

# Backward compatibility alias
PRIVATE_PLATFORMS = AUCTION_PLATFORMS


# ---------------------------------------------------------------------------
# Стратегії пошуку — де і як шукати NPL-портфелі
# ---------------------------------------------------------------------------

SEARCH_STRATEGIES = [
    {
        "name": "ProZorro.Sale — пряме сканування",
        "priority": "high",
        "description": "Регулярно моніторити ProZorro.Sale за ключовими словами. "
                       "Всі державні банки та ФГВ зобов'язані продавати тут.",
        "keywords": [
            "право вимоги", "права вимоги", "кредитний портфель",
            "портфель прав вимоги", "непрацюючі активи",
            "дебіторська заборгованість", "відступлення",
        ],
        "target_url": "https://prozorro.sale/auction/search?query=%D0%BF%D1%80%D0%B0%D0%B2%D0%BE+%D0%B2%D0%B8%D0%BC%D0%BE%D0%B3%D0%B8",
    },
    {
        "name": "SETAM — пошук лотів",
        "priority": "high",
        "description": "SETAM продає арештоване майно, але іноді з'являються портфелі прав вимоги.",
        "keywords": ["право вимоги", "портфель", "кредитний"],
        "target_url": "https://setam.net.ua/auctions",
    },
    {
        "name": "Судовий реєстр — відстеження угод",
        "priority": "medium",
        "description": "Шукати рішення судів де згадується 'договір відступлення прав вимоги' + назва банку. "
                       "Це показує які банки продавали портфелі і кому.",
        "keywords": [
            "договір відступлення права вимоги",
            "відступлення прав вимоги за кредитним договором",
            "купівля-продаж прав вимоги",
        ],
        "target_url": "https://reyestr.court.gov.ua",
    },
    {
        "name": "АМКУ — рішення про концентрацію",
        "priority": "medium",
        "description": "Великі NPL-угоди потребують дозволу АМКУ. Рішення розкривають деталі: "
                       "хто покупець, який банк продавець, обсяг портфеля.",
        "keywords": [
            "відступлення прав вимоги",
            "кредитний портфель",
            "фінансова компанія",
        ],
        "target_url": "https://amcu.gov.ua/napryami/konkurentne-zakonodavstvo/kontsentratsiyi",
    },
    {
        "name": "НКЦПФР / stockmarket.gov.ua — звіти ФК",
        "priority": "medium",
        "description": "Фінансові компанії зобов'язані розкривати суттєву інформацію. "
                       "Купівля великого NPL-портфеля = суттєва подія → звіт на stockmarket.gov.ua.",
        "keywords": [
            "придбання прав вимоги",
            "портфель",
            "факторинг",
        ],
        "target_url": "https://stockmarket.gov.ua",
    },
    {
        "name": "ФГВ — новини та звіти",
        "priority": "high",
        "description": "ФГВ регулярно публікує оголошення про продаж активів ліквідованих банків. "
                       "Перевіряти розділ новин та розділ управління активами.",
        "keywords": [
            "реалізація активів", "продаж активів",
            "право вимоги", "портфель",
        ],
        "target_url": "https://www.fg.gov.ua/news",
    },
    {
        "name": "Банківські сайти — розділи продажу активів",
        "priority": "medium",
        "description": "Деякі банки мають окремі сторінки 'Продаж активів' або 'Управління проблемними активами'. "
                       "Скрапер автоматично сканує зареєстровані банки за ключовими словами.",
        "keywords": [
            "продаж активів", "непрацюючі активи",
            "проблемні активи", "workout",
            "тендер", "аукціон",
        ],
        "target_url": "",
    },
    {
        "name": "МФО — фінансова звітність",
        "priority": "low",
        "description": "Великі МФО (Манівео, MyCredit, CCloan) продають портфелі на закритих торгах. "
                       "Інформацію можна знайти в їхній квартальній/річній фінзвітності та примітках до неї.",
        "keywords": [
            "продаж портфеля", "відступлення",
            "реструктуризація портфеля",
        ],
        "target_url": "",
    },
    {
        "name": "Перевірка покупців ФГВ-портфелів",
        "priority": "medium",
        "description": "Знайти ФК які купували портфелі ФГВ з 2020 року. Перевірити через судовий реєстр "
                       "чи ця ФК подавала позови / виконавчі написи. Якщо ні — портфель може бути на перепродажі.",
        "keywords": [],
        "target_url": "https://reyestr.court.gov.ua",
    },
    {
        "name": "Моніторинг великих ФК на перепродаж",
        "priority": "medium",
        "description": "Великі ФК-колектори (Форінт, Укрборг, тощо) іноді перепродають частини портфелів "
                       "іншим ФК. Відстежувати через АМКУ, суди, та прямий контакт.",
        "keywords": [],
        "target_url": "",
    },
]


# ---------------------------------------------------------------------------
# Bank website scraper
# ---------------------------------------------------------------------------


class BankSiteScraper(BaseScraper):
    """Scan bank websites for NPL sale announcements."""

    def scan_bank(self, config: BankConfig) -> List[Dict[str, Any]]:
        """Scan a single bank's website for NPL-related pages."""
        results: List[Dict[str, Any]] = []
        pages_to_scan = []

        if config.npl_page:
            pages_to_scan.append(("npl_page", config.npl_page))
        if config.news_page:
            pages_to_scan.append(("news", config.news_page))
        if config.accreditation_page:
            pages_to_scan.append(("accreditation", config.accreditation_page))

        # Fallback: scan main website
        if not pages_to_scan:
            pages_to_scan.append(("main", config.website))

        for page_type, url in pages_to_scan:
            html = self.safe_fetch(url)
            if not html:
                continue
            links = extract_links(html, config.website, keywords=config.keywords)
            for text, href in links:
                if not any(r["url"] == href for r in results):
                    results.append({
                        "bank": config.short_name,
                        "bank_type": config.bank_type,
                        "title": text,
                        "url": href,
                        "page_type": page_type,
                        "source_url": url,
                    })

        LOGGER.info("Bank scan %s: found %d relevant links", config.short_name, len(results))
        return results

    def scan_all_banks(self, bank_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Scan all registered banks, optionally filtered by type."""
        all_results: List[Dict[str, Any]] = []
        for config in BANK_REGISTRY:
            if bank_types and config.bank_type not in bank_types:
                continue
            results = self.scan_bank(config)
            all_results.extend(results)
        return all_results


def get_accreditation_info() -> List[Dict[str, str]]:
    """Return known accreditation requirements for banks with internal auctions."""
    info = []
    for config in BANK_REGISTRY:
        if config.accreditation_page or "акредит" in config.notes.lower() or "внутрішн" in config.notes.lower():
            info.append({
                "bank": config.short_name,
                "name": config.name,
                "accreditation_page": config.accreditation_page or "",
                "notes": config.notes,
                "website": config.website,
            })
    return info


# ---------------------------------------------------------------------------
# Додаткові джерела для верифікації та аналітики
# Всі URL — реальні діючі ресурси.
# ---------------------------------------------------------------------------

VERIFICATION_SOURCES = [
    {
        "name": "YouControl — система аналітики та перевірки компаній",
        "url": "https://youcontrol.com.ua",
        "description": "Комерційна платформа бізнес-аналітики. Зведена інформація з ЄДР, податкової, "
                       "судового реєстру, виконавчих проваджень, санкційних списків. "
                       "Перевірка юросіб-боржників та ФК-покупців.",
        "type": "verification",
    },
    {
        "name": "Clarity Project — аналітика публічних закупівель",
        "url": "https://clarity-project.info",
        "description": "Аналітика ProZorro та ProZorro.Sale. Зручний пошук по тендерах, "
                       "включаючи продажі активів банків. Можна шукати по продавцю, ключовим словам.",
        "type": "analytics",
    },
    {
        "name": "НБУ — Реєстр банків та ліцензій",
        "url": "https://bank.gov.ua/ua/supervision/registry",
        "description": "Офіційний реєстр всіх діючих банків України з ліцензіями. "
                       "Тут же список банків, що ліквідуються, та банків з тимчасовою адміністрацією.",
        "type": "registry",
    },
    {
        "name": "НБУ — Дані наглядової статистики",
        "url": "https://bank.gov.ua/ua/statistic/supervision-statist",
        "description": "Показники фінансової стійкості банків, включаючи обсяги NPL. "
                       "Дозволяє зрозуміти у яких банків найбільше проблемних кредитів.",
        "type": "analytics",
    },
    {
        "name": "Єдиний державний реєстр юридичних осіб (ЄДР)",
        "url": "https://usr.minjust.gov.ua",
        "description": "Офіційний реєстр Мін'юсту. Інформація про реєстрацію, статус, засновників, "
                       "види діяльності юросіб.",
        "type": "registry",
    },
    {
        "name": "Реєстр виконавчих проваджень (АSVP)",
        "url": "https://asvpweb.minjust.gov.ua",
        "description": "Автоматизована система виконавчих проваджень. Пошук відкритих виконавчих "
                       "проваджень по боржниках.",
        "type": "verification",
    },
    {
        "name": "Єдиний реєстр боржників",
        "url": "https://erb.minjust.gov.ua",
        "description": "Реєстр боржників у виконавчих провадженнях Мін'юсту.",
        "type": "verification",
    },
    {
        "name": "Державний реєстр обтяжень рухомого майна",
        "url": "https://orm.minjust.gov.ua",
        "description": "Перевірка наявності обтяжень на майні боржників. Корисно для оцінки "
                       "забезпечених кредитів у портфелі.",
        "type": "verification",
    },
    {
        "name": "Державний реєстр речових прав на нерухоме майно",
        "url": "https://kap.minjust.gov.ua",
        "description": "Перевірка прав власності та обтяжень на нерухомість боржників. "
                       "Критично для оцінки іпотечних портфелів.",
        "type": "verification",
    },
]


# ---------------------------------------------------------------------------
# Банки під ліквідацією ФГВ — їх портфелі продаються через ProZorro.Sale
# Це публічна інформація з сайту ФГВ (fg.gov.ua).
# Шукати на ProZorro.Sale за назвою кожного банку як продавця.
# ---------------------------------------------------------------------------

DGF_LIQUIDATED_BANKS = [
    {"name": "ПАТ «Дельта Банк»", "year_liquidation_start": 2015},
    {"name": "ПАТ «Банк Фінанси та Кредит»", "year_liquidation_start": 2015},
    {"name": "АТ «Банк «Фінансова Ініціатива»", "year_liquidation_start": 2015},
    {"name": "ПАТ «Імексбанк»", "year_liquidation_start": 2015},
    {"name": "ПАТ «Надра Банк»", "year_liquidation_start": 2015},
    {"name": "ПАТ «КБ «Хрещатик»", "year_liquidation_start": 2016},
    {"name": "ПАТ «Банк Михайлівський»", "year_liquidation_start": 2016},
    {"name": "ПАТ «Платинум Банк»", "year_liquidation_start": 2017},
    {"name": "ПАТ «ВіЕйБі Банк»", "year_liquidation_start": 2015},
    {"name": "ПАТ «Брокбізнесбанк»", "year_liquidation_start": 2014},
    {"name": "ПАТ «Банк Форум»", "year_liquidation_start": 2014},
    {"name": "ПАТ «Актабанк»", "year_liquidation_start": 2014},
    {"name": "ПАТ «Банк Камбіо»", "year_liquidation_start": 2015},
    {"name": "ПАТ «ПроФін Банк»", "year_liquidation_start": 2015},
    {"name": "ПАТ «Златобанк»", "year_liquidation_start": 2015},
    {"name": "ПАТ «Євробанк»", "year_liquidation_start": 2014},
    {"name": "ПАТ «Фідобанк»", "year_liquidation_start": 2016},
    {"name": "ПАТ «Діамантбанк»", "year_liquidation_start": 2017},
    {"name": "ПАТ «Банк Богуслав»", "year_liquidation_start": 2016},
    {"name": "ПАТ «Укрінбанк»", "year_liquidation_start": 2015},
    {"name": "АТ «Банк Січ»", "year_liquidation_start": 2022},
]


# ---------------------------------------------------------------------------
# Розширені ключові слова для пошуку NPL на різних платформах
# ---------------------------------------------------------------------------

SEARCH_KEYWORDS = {
    "prozorro_sale": [
        "право вимоги",
        "права вимоги",
        "портфель прав вимоги",
        "кредитний портфель",
        "непрацюючі активи",
        "дебіторська заборгованість",
        "відступлення прав вимоги",
        "пул кредитів",
        "реалізація активів банку",
        "активи неплатоспроможного банку",
    ],
    "court_registry": [
        "договір відступлення права вимоги",
        "відступлення прав вимоги за кредитним договором",
        "купівля-продаж прав вимоги",
        "факторинг",
        "цесія",
        "новий кредитор",
        "заміна кредитора",
        "правонаступник банку",
    ],
    "amcu": [
        "набуття права вимоги",
        "придбання активів",
        "відступлення прав вимоги",
        "кредитний портфель",
        "концентрація",
        "фінансова компанія",
    ],
    "bank_sites": [
        "продаж активів",
        "реалізація активів",
        "непрацюючі активи",
        "проблемні активи",
        "тендер",
        "аукціон",
        "конкурс з продажу",
        "workout",
        "управління проблемною заборгованістю",
        "запрошення до участі",
        "оголошення про продаж",
        "портфель",
    ],
    "nkcpfr_reports": [
        "відступлення прав вимоги",
        "придбання портфеля",
        "факторингові операції",
        "суттєва інформація",
        "значний правочин",
    ],
    "mfo_reports": [
        "продаж портфеля",
        "відступлення прав вимоги",
        "реструктуризація портфеля",
        "списання заборгованості",
        "передача колекторській компанії",
    ],
}
