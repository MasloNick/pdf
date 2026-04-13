"""Known NPL auction lots — ТІЛЬКИ перевірені дані.

Джерела підтвердження:
- "screenshot" — користувач показав скріншот сторінки
- "websearch_meta" — WebSearch повернув конкретні дані зі сторінки
- "scraper_live" — скрапер знайшов на ПК користувача в реальному часі

НЕ додаємо лоти де:
- Дата взята з ID аукціону (це дата ПУБЛІКАЦІЇ, не проведення)
- Сума вигадана або порахована приблизно
- Статус не підтверджений
"""

LOTS = [

    # ================================================================
    # ПІДТВЕРДЖЕНО: скріншот користувача 13.04.2026
    # ================================================================

    {"category": "history",
     "source": "SETAM/ПриватБанк",
     "seller": "АТ КБ «ПриватБанк»",
     "what": "Продаж права вимоги за портфелем карткових кредитів фіз.осіб — 80 545 договорів",
     "title": "SETAM 541272 | ПриватБанк 80 545 карток",
     "url": "https://setam.net.ua/auction/541272",
     "asset_type": "npl_credit_unsecured",
     "num_contracts": 80545,
     "total_debt": 501395467.60,
     "start_price": 501395467.60,
     "avg_debt": 6225.0,
     "sold_price": 13101000.00,
     "sold_pct": 2.6,
     "auction_type": "Редукціон",
     "guarantee": "526 465.24 грн",
     "auction_date": "2024-02-23",
     "auction_time": "09:00",
     "status": "продано 23.02.2024 за 13 101 000 грн",
     "verified": "screenshot"},

    # ================================================================
    # ПІДТВЕРДЖЕНО: WebSearch повернув конкретні дані
    # ================================================================

    {"category": "watching",
     "source": "SETAM/Укрексімбанк",
     "seller": "АТ «Укрексімбанк»",
     "what": "Права вимоги за кредитами до юр.осіб (РАІЗ-МАКСИМКО, АВАНГАРД, ІМПЕРОВО ФУДЗ, ПАККО ХОЛДІНГ)",
     "title": "SETAM 564348 | Укрексімбанк юр.особи",
     "url": "https://setam.net.ua/auction/564348",
     "asset_type": "npl_credit_corporate",
     "num_contracts": None,
     "total_debt": 4984663467.30,
     "start_price": 4984663467.30,
     "avg_debt": None,
     "auction_type": "Редукціон",
     "guarantee": "74 769 952.01 грн",
     "auction_date": "2025-03-07",
     "auction_time": "09:00",
     "status": "не відбувся 07.03.2025",
     "watch_reason": "Аукціон не відбувся — очікується перевиставлення зі зниженою ціною.",
     "auctions_passed": 1,
     "verified": "websearch_meta"},

    {"category": "history",
     "source": "SETAM/ПриватБанк",
     "seller": "АТ КБ «ПриватБанк»",
     "what": "Права вимоги за беззаставними кредитами фіз.осіб",
     "title": "SETAM 576099 | ПриватБанк фіз.осіб",
     "url": "https://setam.net.ua/auction/576099",
     "asset_type": "npl_credit_unsecured",
     "num_contracts": None,
     "total_debt": 5203956695.69,
     "start_price": 5203956695.69,
     "avg_debt": None,
     "auction_type": "Редукціон",
     "guarantee": "",
     "auction_date": "",
     "status": "торги відбулися",
     "verified": "websearch_meta"},

    {"category": "history",
     "source": "ProZorro",
     "seller": "Банк",
     "what": "Кредитний портфель — права вимоги за кредитами юр.осіб",
     "title": "CSD001-UA-20250711 | Портфель юр.осіб",
     "url": "https://prozorro.sale/auction/CSD001-UA-20250711-29449/",
     "asset_type": "npl_credit_corporate",
     "num_contracts": None,
     "total_debt": None,
     "start_price": 178110088.04,
     "avg_debt": None,
     "sold_price": 28497614.09,
     "sold_pct": 16.0,
     "auction_type": "Гібридний голландський",
     "guarantee": "",
     "auction_date": "2025-07-11",
     "status": "продано за 16% від стартової",
     "verified": "websearch_meta"},

    {"category": "watching",
     "source": "ProZorro/ФГВ",
     "seller": "ФГВ",
     "what": "Пул: права вимоги за кредитами фіз.осіб + дебіторка юр.осіб + ОЗ + транспорт",
     "title": "GFD001-UA-20260205 | ФГВ пул активів",
     "url": "https://prozorro.sale/auction/GFD001-UA-20260205-03708/",
     "asset_type": "asset_pool",
     "num_contracts": None,
     "total_debt": None,
     "start_price": 8457238.13,
     "avg_debt": None,
     "auction_type": "Голландський (ФГВ)",
     "guarantee": "",
     "auction_date": "",
     "status": "не відбувся",
     "watch_reason": "Перший аукціон не відбувся. Буде перевиставлений.",
     "auctions_passed": 1,
     "verified": "websearch_meta"},

    {"category": "watching",
     "source": "ProZorro/ФГВ",
     "seller": "ФГВ",
     "what": "Дебіторська заборгованість суб'єкта за договором №71 — 26 903 628 грн",
     "title": "GFD001-UA-20250127 | Дебіторка 26.9M",
     "url": "https://prozorro.sale/auction/GFD001-UA-20250127-81006/",
     "asset_type": "receivable",
     "num_contracts": 1,
     "total_debt": 26903628.26,
     "start_price": 26903628.26,
     "avg_debt": 26903628.26,
     "auction_type": "Голландський (ФГВ)",
     "guarantee": "",
     "auction_date": "",
     "status": "не відбувся",
     "watch_reason": "Великий лот. Не відбувся — потенційно перевиставиться дешевше.",
     "auctions_passed": 1,
     "verified": "websearch_meta"},

    {"category": "active",
     "source": "ProZorro/Комерційний",
     "seller": "—",
     "what": "Пул: права вимоги за кредитними та телеком-договорами з фіз./юр.особами — 14 366 договорів",
     "title": "CSE001-UA-20260317 | Пул 14 366 договорів",
     "url": "https://prozorro.sale/auction/CSE001-UA-20260317-02812/",
     "asset_type": "mixed",
     "num_contracts": 14366,
     "total_debt": None,
     "start_price": None,
     "avg_debt": None,
     "auction_type": "Комерційний (зниження ціни)",
     "guarantee": "",
     "auction_date": "",
     "status": "активний — перевірити на сайті",
     "verified": "websearch_meta"},

    {"category": "active",
     "source": "ProZorro/Банк",
     "seller": "Банк (Ощадбанк)",
     "what": "Продаж боргу / відступлення права вимоги до фіз.особи за кредитним договором (автокредит із забезпеченням)",
     "title": "NLE001-UA-20251229 | Автокредит 148K",
     "url": "https://prozorro.sale/auction/NLE001-UA-20251229-34113/",
     "asset_type": "npl_credit_secured",
     "num_contracts": 1,
     "total_debt": 148767.64,
     "start_price": 148767.64,
     "avg_debt": 148767.64,
     "auction_type": "Англійський (3 раунди)",
     "guarantee": "",
     "auction_date": "",
     "status": "активний — перевірити на сайті",
     "verified": "websearch_meta"},

    # ================================================================
    # Решту лотів знаходить скрапер АВТОМАТИЧНО з твого ПК
    # (UBIZ 11+ лотів, ФГВ 15+ лотів, SETAM 1+ лот)
    # Вони НЕ захардкожені — оновлюються при кожному скануванні
    # ================================================================
]
