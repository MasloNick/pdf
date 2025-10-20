-- Схема бази даних для адрес України та судової юрисдикції

-- Таблиця областей України
CREATE TABLE IF NOT EXISTS oblasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_en TEXT,
    koatuu_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця районів
CREATE TABLE IF NOT EXISTS raions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    oblast_id INTEGER NOT NULL,
    koatuu_code TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (oblast_id) REFERENCES oblasts(id),
    UNIQUE(name, oblast_id)
);

-- Таблиця населених пунктів (міста, селища, села)
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT CHECK(type IN ('місто', 'селище міського типу', 'селище', 'село')),
    oblast_id INTEGER NOT NULL,
    raion_id INTEGER,
    koatuu_code TEXT,
    population INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (oblast_id) REFERENCES oblasts(id),
    FOREIGN KEY (raion_id) REFERENCES raions(id)
);

-- Таблиця місцевих судів загальної юрисдикції першої інстанції
CREATE TABLE IF NOT EXISTS courts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    full_name TEXT,
    type TEXT CHECK(type IN ('районний', 'міський', 'міськрайонний', 'окружний')) DEFAULT 'районний',
    address TEXT,
    phone TEXT,
    email TEXT,
    website TEXT,
    head_judge TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця юрисдикції (зв'язок територій з судами)
CREATE TABLE IF NOT EXISTS jurisdiction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,
    oblast_id INTEGER,
    raion_id INTEGER,
    settlement_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES courts(id),
    FOREIGN KEY (oblast_id) REFERENCES oblasts(id),
    FOREIGN KEY (raion_id) REFERENCES raions(id),
    FOREIGN KEY (settlement_id) REFERENCES settlements(id),
    -- Принаймні один з territory полів має бути заповнений
    CHECK (oblast_id IS NOT NULL OR raion_id IS NOT NULL OR settlement_id IS NOT NULL)
);

-- Індекси для прискорення пошуку
CREATE INDEX IF NOT EXISTS idx_raions_oblast ON raions(oblast_id);
CREATE INDEX IF NOT EXISTS idx_settlements_oblast ON settlements(oblast_id);
CREATE INDEX IF NOT EXISTS idx_settlements_raion ON settlements(raion_id);
CREATE INDEX IF NOT EXISTS idx_jurisdiction_court ON jurisdiction(court_id);
CREATE INDEX IF NOT EXISTS idx_jurisdiction_settlement ON jurisdiction(settlement_id);
CREATE INDEX IF NOT EXISTS idx_jurisdiction_raion ON jurisdiction(raion_id);
CREATE INDEX IF NOT EXISTS idx_jurisdiction_oblast ON jurisdiction(oblast_id);

-- Представлення для зручного пошуку підсудності
CREATE VIEW IF NOT EXISTS address_jurisdiction AS
SELECT
    s.id as settlement_id,
    s.name as settlement_name,
    s.type as settlement_type,
    r.id as raion_id,
    r.name as raion_name,
    o.id as oblast_id,
    o.name as oblast_name,
    c.id as court_id,
    c.name as court_name,
    c.full_name as court_full_name,
    c.type as court_type,
    c.address as court_address,
    c.phone as court_phone,
    c.email as court_email,
    c.website as court_website
FROM settlements s
LEFT JOIN raions r ON s.raion_id = r.id
LEFT JOIN oblasts o ON s.oblast_id = o.id
LEFT JOIN jurisdiction j ON (j.settlement_id = s.id OR j.raion_id = r.id OR j.oblast_id = o.id)
LEFT JOIN courts c ON j.court_id = c.id;
