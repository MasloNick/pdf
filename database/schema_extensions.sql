-- Розширення схеми бази даних для альтернативних назв та переміщених судів

-- Таблиця альтернативних назв населених пунктів (для перейменувань)
CREATE TABLE IF NOT EXISTS settlement_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    settlement_id INTEGER NOT NULL,
    alias_name TEXT NOT NULL,
    alias_type TEXT CHECK(alias_type IN ('старе_офіційне', 'історичне', 'транслітерація', 'народне')) DEFAULT 'старе_офіційне',
    valid_from DATE,
    valid_to DATE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (settlement_id) REFERENCES settlements(id),
    UNIQUE(settlement_id, alias_name)
);

-- Таблиця альтернативних назв районів
CREATE TABLE IF NOT EXISTS raion_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raion_id INTEGER NOT NULL,
    alias_name TEXT NOT NULL,
    valid_from DATE,
    valid_to DATE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (raion_id) REFERENCES raions(id),
    UNIQUE(raion_id, alias_name)
);

-- Таблиця районів міст (внутрішні адміністративні райони)
CREATE TABLE IF NOT EXISTS city_districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    settlement_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (settlement_id) REFERENCES settlements(id),
    UNIQUE(name, settlement_id)
);

-- Таблиця тимчасово переміщених судів
CREATE TABLE IF NOT EXISTS displaced_courts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,
    original_oblast_id INTEGER,
    original_raion_id INTEGER,
    original_settlement_id INTEGER,
    original_address TEXT,
    current_oblast_id INTEGER,
    current_raion_id INTEGER,
    current_settlement_id INTEGER,
    current_address TEXT,
    displacement_date DATE,
    reason TEXT,
    status TEXT CHECK(status IN ('тимчасово_переміщений', 'повернувся', 'закритий')) DEFAULT 'тимчасово_переміщений',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES courts(id),
    FOREIGN KEY (original_oblast_id) REFERENCES oblasts(id),
    FOREIGN KEY (original_raion_id) REFERENCES raions(id),
    FOREIGN KEY (original_settlement_id) REFERENCES settlements(id),
    FOREIGN KEY (current_oblast_id) REFERENCES oblasts(id),
    FOREIGN KEY (current_raion_id) REFERENCES raions(id),
    FOREIGN KEY (current_settlement_id) REFERENCES settlements(id)
);

-- Таблиця історії назв судів
CREATE TABLE IF NOT EXISTS court_name_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    court_id INTEGER NOT NULL,
    old_name TEXT NOT NULL,
    valid_from DATE,
    valid_to DATE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_id) REFERENCES courts(id)
);

-- Індекси для прискорення пошуку
CREATE INDEX IF NOT EXISTS idx_settlement_aliases_settlement ON settlement_aliases(settlement_id);
CREATE INDEX IF NOT EXISTS idx_settlement_aliases_name ON settlement_aliases(alias_name);
CREATE INDEX IF NOT EXISTS idx_raion_aliases_raion ON raion_aliases(raion_id);
CREATE INDEX IF NOT EXISTS idx_city_districts_settlement ON city_districts(settlement_id);
CREATE INDEX IF NOT EXISTS idx_displaced_courts_court ON displaced_courts(court_id);
CREATE INDEX IF NOT EXISTS idx_displaced_courts_status ON displaced_courts(status);
CREATE INDEX IF NOT EXISTS idx_court_name_history_court ON court_name_history(court_id);

-- Представлення для пошуку з альтернативними назвами
CREATE VIEW IF NOT EXISTS settlements_with_aliases AS
SELECT
    s.*,
    GROUP_CONCAT(sa.alias_name, '; ') as aliases
FROM settlements s
LEFT JOIN settlement_aliases sa ON s.id = sa.settlement_id
GROUP BY s.id;
