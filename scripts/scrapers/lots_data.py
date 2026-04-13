"""Known NPL auction lots — verified data as of 13.04.2026.

Each lot has category: active / watching / history.
Sorted by date within each category (newest first).
"""

LOTS = [

    # ================================================================
    # АКТУАЛЬНІ — квітень 2026
    # ================================================================

    # --- КС Фортеця — 12 квітня 2026 (нові лоти!) ---
    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Макаренко В.С. — 716 739 грн", "title": "BRE001-UA-20260412-93803 | Макаренко 716K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260412-93803",
     "num_contracts": 1, "total_debt": 716739.33, "start_price": 716739.33, "avg_debt": 716739.33,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 35 837 грн",
     "auction_date": "2026-04-12", "status": "12.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Ковтун Ю.О. — 448 343 грн", "title": "BRE001-UA-20260412-57322 | Ковтун 448K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260412-57322",
     "num_contracts": 1, "total_debt": 448343.56, "start_price": 448343.56, "avg_debt": 448343.56,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 22 417 грн",
     "auction_date": "2026-04-12", "status": "12.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Кондратенко П.А. — 5 057 грн", "title": "BRE001-UA-20260412-18603 | Кондратенко 5K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260412-18603",
     "num_contracts": 1, "total_debt": 5057.02, "start_price": 5057.02, "avg_debt": 5057.02,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 253 грн",
     "auction_date": "2026-04-12", "status": "12.04.2026"},

    # --- КС Фортеця — 10 квітня 2026 ---
    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Магай Г.В. — 777 625 грн", "title": "BRE001-UA-20260410-57627 | Магай 777K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260410-57627",
     "num_contracts": 1, "total_debt": 777625.66, "start_price": 777625.66, "avg_debt": 777625.66,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 38 881 грн",
     "auction_date": "2026-04-10", "status": "10.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Ковтун Ю.О. — 303 866 грн", "title": "BRE001-UA-20260410-83171 | Ковтун 303K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260410-83171",
     "num_contracts": 1, "total_debt": 303866.14, "start_price": 303866.14, "avg_debt": 303866.14,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 15 193 грн",
     "auction_date": "2026-04-10", "status": "10.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Степаненко А.П. — 155 047 грн", "title": "BRE001-UA-20260410-06629 | Степаненко 155K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260410-06629",
     "num_contracts": 1, "total_debt": 155047.24, "start_price": 155047.24, "avg_debt": 155047.24,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 7 752 грн",
     "auction_date": "2026-04-10", "status": "10.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "КС «Фортеця»",
     "what": "Дебіторка до Пушкаренко С.М. — 82 254 грн", "title": "BRE001-UA-20260410-28967 | Пушкаренко 82K",
     "url": "https://ubiz.ua/sale3/auction/BRE001-UA-20260410-28967",
     "num_contracts": 1, "total_debt": 82254.59, "start_price": 82254.59, "avg_debt": 82254.59,
     "auction_type": "Англійський (3 раунди)", "guarantee": "5% = 4 113 грн",
     "auction_date": "2026-04-10", "status": "10.04.2026"},

    # --- Банкрутства — квітень 2026 ---
    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ТОВ «ФКТН АГРО ПЛЮС»",
     "what": "Дебіторка ТОВ «РОСКО ТРЕЙД» (ЄДРПОУ 36673556, Одеса) — 373 322 грн",
     "title": "BRD001-UA-20260409-32348 | РОСКО ТРЕЙД 373K",
     "url": "https://ubiz.ua/sale3/auction/BRD001-UA-20260409-32348",
     "num_contracts": 1, "total_debt": 373322.38, "start_price": 373322.38, "avg_debt": 373322.38,
     "auction_type": "Голландський (зниження ціни)", "guarantee": "5% = 18 666 грн",
     "auction_date": "2026-04-09", "status": "09.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ТОВ «ФКТН АГРО ПЛЮС»",
     "what": "Дебіторка ФОП Стужук А.М. — 228 319 грн",
     "title": "BRD001-UA-20260409-11003 | ФОП Стужук 228K",
     "url": "https://ubiz.ua/sale3/auction/BRD001-UA-20260409-11003",
     "num_contracts": 1, "total_debt": 228319.00, "start_price": 228319.00, "avg_debt": 228319.00,
     "auction_type": "Англійський аукціон", "guarantee": "5% = 11 416 грн",
     "auction_date": "2026-04-09", "status": "09.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ПрАТ «ТРЕСТ КРИВБАСШАХТОПРОХОДКА»",
     "what": "Право вимоги (зобов'язання) в процедурі банкрутства",
     "title": "BRD001-UA-20260407-93201 | КРИВБАСШАХТОПРОХОДКА",
     "url": "https://ubiz.ua/sale3/auction/BRD001-UA-20260407-93201",
     "num_contracts": None, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Голландський (зниження ціни)", "guarantee": "",
     "auction_date": "2026-04-07", "status": "07.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ТМО «СЛОВ'ЯНСЬК»",
     "what": "Право вимоги (зобов'язання) в процедурі банкрутства",
     "title": "BRD001-UA-20260407-97730 | ТМО СЛОВ'ЯНСЬК",
     "url": "https://ubiz.ua/sale3/auction/BRD001-UA-20260407-97730",
     "num_contracts": None, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Голландський (зниження ціни)", "guarantee": "",
     "auction_date": "2026-04-07", "status": "07.04.2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ФГ «РВВ» (ЄДРПОУ 37015473, Одеса)",
     "what": "Право вимоги (дебіторська заборгованість) фермерського господарства",
     "title": "BRD001-UA-20260406-23304 | ФГ РВВ Одеса",
     "url": "https://ubiz.ua/sale3/auction/BRD001-UA-20260406-23304",
     "num_contracts": 1, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Голландський (зниження ціни)", "guarantee": "",
     "auction_date": "2026-04-06", "status": "06.04.2026"},

    # --- Великі портфелі ---
    {"category": "active", "source": "ProZorro/Комерційний", "seller": "—",
     "what": "Пул: права вимоги за кредитними та телеком-договорами з фіз./юр. особами — 14 366 договорів",
     "title": "CSE001-UA-20260317-02812 | Пул 14 366 договорів",
     "url": "https://prozorro.sale/auction/CSE001-UA-20260317-02812/",
     "num_contracts": 14366, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Комерційний (зниження ціни)", "guarantee": "",
     "auction_date": "2026-03-17", "status": "активний"},

    {"category": "active", "source": "ProZorro/Комерційний", "seller": "—",
     "what": "Пул: права вимоги за кредитними та телеком-договорами — 14 038 договорів (Київ)",
     "title": "CSE001-UA-20260317-24027 | Пул 14 038 договорів",
     "url": "https://ubiz.ua/en/sale3/auction/CSE001-UA-20260317-24027",
     "num_contracts": 14038, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Комерційний (зниження ціни)", "guarantee": "",
     "auction_date": "2026-03-17", "status": "активний"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ТОВ «ВЕСТ СТАНДАРТ ЮА»",
     "what": "Право вимоги до АТ «Укрбудінвестбанк» (2-й повторний аукціон)",
     "title": "BRD001-UA-20260328-53605 | до Укрбудінвестбанку",
     "url": "https://ubiz.ua/sale3/auction/BRD001-UA-20260328-53605",
     "num_contracts": 1, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Голландський (2-й повторний)", "guarantee": "",
     "auction_date": "2026-03-28", "status": "березень 2026"},

    {"category": "active", "source": "ProZorro/Банкрутство", "seller": "ТОВ «ФК Інвестохіллс Веста»",
     "what": "Майно банкрута — фінансова компанія (ЄДРПОУ 41264766)",
     "title": "BRE001-UA-20260317-96276 | ФК Інвестохіллс Веста",
     "url": "https://ubiz.ua/en/sale3/auction/BRE001-UA-20260317-96276",
     "num_contracts": None, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Англійський аукціон", "guarantee": "",
     "auction_date": "2026-03-17", "status": "березень 2026"},

    {"category": "active", "source": "ProZorro/Банк", "seller": "Банк (через Ощадбанк)",
     "what": "Продаж боргу / відступлення права вимоги до фіз.особи (автокредит із забезпеченням) — 148 767 грн",
     "title": "NLE001-UA-20251229-34113 | Автокредит 148K",
     "url": "https://prozorro.sale/auction/NLE001-UA-20251229-34113/",
     "num_contracts": 1, "total_debt": 148767.64, "start_price": 148767.64, "avg_debt": 148767.64,
     "auction_type": "Англійський (3 раунди)", "guarantee": "",
     "auction_date": "", "status": "активний"},

    # --- ФГВ ---
    {"category": "active", "source": "ProZorro/ФГВ", "seller": "ФГВ",
     "what": "Пул: 409 беззаставних кредитів фіз.осіб + 2504 актива дебіторки + кредити юр.осіб",
     "title": "GFD001-UA-20260217-57143 | ФГВ пул 409+2504",
     "url": "https://ubiz.ua/sale3/auction/GFD001-UA-20260217-57143",
     "num_contracts": 2913, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Голландський (ФГВ)", "guarantee": "",
     "auction_date": "2026-02-17", "status": "активний/перевірити"},

    {"category": "active", "source": "ProZorro/ФГВ", "seller": "ФГВ (КСГ Банк + Банк Форвард)",
     "what": "Пул активів КСГ Банк та Банк Форвард",
     "title": "GFD001-UA-20250506-52157 | ФГВ КСГ+Форвард",
     "url": "https://prozorro.sale/auction/GFD001-UA-20250506-52157/",
     "num_contracts": None, "total_debt": None, "start_price": None, "avg_debt": None,
     "auction_type": "Голландський (ФГВ)", "guarantee": "",
     "auction_date": "2025-05-06", "status": "перевірити"},

    # ================================================================
    # НА СПОСТЕРЕЖЕННІ — не відбулися, очікується перевиставлення
    # ================================================================

    {"category": "watching", "source": "SETAM/Укрексімбанк", "seller": "АТ «Укрексімбанк»",
     "what": "Права вимоги за кредитами до юр.осіб (РАІЗ-МАКСИМКО, АВАНГАРД, ІМПЕРОВО ФУДЗ, ПАККО ХОЛДІНГ)",
     "title": "SETAM 564348 | Укрексімбанк юр.особи (НЕ ВІДБУВСЯ)",
     "url": "https://setam.net.ua/auction/564348",
     "num_contracts": None, "total_debt": 4984663467.30, "start_price": 4984663467.30, "avg_debt": None,
     "auction_type": "Редукціон", "guarantee": "74 769 952.01 грн",
     "auction_date": "2025-03-07", "status": "не відбувся 07.03.2025",
     "watch_reason": "Аукціон не відбувся — очікується перевиставлення зі зниженою ціною. Борг 4.98 млрд грн.",
     "auctions_passed": 1, "auctions_expected": 2},

    {"category": "watching", "source": "ProZorro/ФГВ", "seller": "ФГВ",
     "what": "Пул: права вимоги за кредитами фіз.осіб + дебіторка юр.осіб + ОЗ + транспорт",
     "title": "GFD001-UA-20260205-03708 | ФГВ пул (НЕ ВІДБУВСЯ)",
     "url": "https://prozorro.sale/auction/GFD001-UA-20260205-03708/",
     "num_contracts": None, "total_debt": None, "start_price": 8457238.13, "avg_debt": None,
     "auction_type": "Голландський (ФГВ)", "guarantee": "~5% = ~422 862 грн",
     "auction_date": "", "status": "не відбувся — слідкуємо",
     "watch_reason": "Перший аукціон не відбувся. Буде перевиставлений зі зниженою ціною.",
     "auctions_passed": 1, "auctions_expected": 2},

    {"category": "watching", "source": "ProZorro/ФГВ", "seller": "ФГВ",
     "what": "Дебіторська заборгованість суб'єкта за договором №71 — 26 903 628 грн",
     "title": "GFD001-UA-20250127-81006 | Дебіторка 26.9M (НЕ ВІДБУВСЯ)",
     "url": "https://prozorro.sale/auction/GFD001-UA-20250127-81006/",
     "num_contracts": 1, "total_debt": 26903628.26, "start_price": 26903628.26, "avg_debt": 26903628.26,
     "auction_type": "Голландський (ФГВ)", "guarantee": "",
     "auction_date": "", "status": "не відбувся",
     "watch_reason": "Великий лот 26.9 млн. Не відбувся — потенційно перевиставиться дешевше.",
     "auctions_passed": 1, "auctions_expected": 2},

    {"category": "watching", "source": "ProZorro/ФГВ", "seller": "ФГВ",
     "what": "Пул активів: права вимоги + дебіторка — стартова 1 392 818 грн (очікується підписання)",
     "title": "GFD001-UA-20241205-81138 | Пул 1.39M (підписання)",
     "url": "https://prozorro.sale/auction/GFD001-UA-20241205-81138/",
     "num_contracts": None, "total_debt": None, "start_price": 1392818.24, "avg_debt": None,
     "auction_type": "Голландський (ФГВ)", "guarantee": "",
     "auction_date": "", "status": "очікує підписання договору",
     "watch_reason": "Аукціон відбувся, очікує підписання. Слідкувати чи не зірветься.",
     "auctions_passed": 1, "auctions_expected": 1},

    # ================================================================
    # ІСТОРІЯ — для аналітики ринкових цін
    # ================================================================

    {"category": "history", "source": "SETAM/ПриватБанк", "seller": "АТ КБ «ПриватБанк»",
     "what": "Права вимоги за портфелем карткових кредитів фіз.осіб — 80 545 договорів",
     "title": "SETAM 541272 | ПриватБанк 80K карток (ПРОДАНО)",
     "url": "https://setam.net.ua/auction/541272",
     "num_contracts": 80545, "total_debt": 501395467.60, "start_price": 501395467.60,
     "avg_debt": 6225.0, "sold_price": 13101000.00, "sold_pct": 2.6,
     "auction_type": "Редукціон", "guarantee": "526 465 грн",
     "auction_date": "2024-02-23", "status": "продано 23.02.2024"},

    {"category": "history", "source": "ProZorro", "seller": "Банк",
     "what": "Кредитний портфель — права вимоги за кредитами юр.осіб",
     "title": "CSD001-UA-20250711-29449 | Портфель юр.осіб (ПРОДАНО)",
     "url": "https://prozorro.sale/auction/CSD001-UA-20250711-29449/",
     "num_contracts": None, "total_debt": None, "start_price": 178110088.04,
     "avg_debt": None, "sold_price": 28497614.09, "sold_pct": 16.0,
     "auction_type": "Гібридний голландський", "guarantee": "",
     "auction_date": "2025-07-11", "status": "продано за 16% від стартової"},

    {"category": "history", "source": "SETAM/ПриватБанк", "seller": "АТ КБ «ПриватБанк»",
     "what": "Права вимоги за беззаставними кредитами фіз.осіб",
     "title": "SETAM 576099 | ПриватБанк фіз.осіб (ВІДБУВСЯ)",
     "url": "https://setam.net.ua/auction/576099",
     "num_contracts": None, "total_debt": 5203956695.69, "start_price": 5203956695.69,
     "avg_debt": None, "sold_price": None, "sold_pct": None,
     "auction_type": "Редукціон", "guarantee": "",
     "auction_date": "", "status": "торги відбулися"},
]
