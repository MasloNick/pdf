#!/usr/bin/env python3
"""
Розширений скрипт для імпорту даних про адреси України та суди в базу даних SQLite
Включає: альтернативні назви, переміщені суди, додаткові міста
"""

import sqlite3
import csv
import os
from pathlib import Path

# Шляхи до файлів
BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / 'database'
DATA_DIR = BASE_DIR / 'data'
DB_PATH = DB_DIR / 'ukraine_addresses.db'
SCHEMA_PATH = DB_DIR / 'schema.sql'
SCHEMA_EXT_PATH = DB_DIR / 'schema_extensions.sql'


def create_database():
    """Створює базу даних з основною схемою"""
    print(f"Створення бази даних: {DB_PATH}")
    DB_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Основна схема
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
        cursor.executescript(schema)

    # Розширення схеми
    if SCHEMA_EXT_PATH.exists():
        print("Застосування розширень схеми...")
        with open(SCHEMA_EXT_PATH, 'r', encoding='utf-8') as f:
            schema_ext = f.read()
            cursor.executescript(schema_ext)

    conn.commit()
    print("База даних створена успішно")
    return conn


def import_oblasts(conn):
    """Імпортує дані про області"""
    print("Імпорт областей...")
    cursor = conn.cursor()

    with open(DATA_DIR / 'oblasts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                "INSERT INTO oblasts (name, name_en, koatuu_code) VALUES (?, ?, ?)",
                (row['name'], row['name_en'], row['koatuu_code'])
            )

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM oblasts").fetchone()[0]
    print(f"Імпортовано {count} областей")


def import_raions(conn):
    """Імпортує дані про райони"""
    print("Імпорт районів...")
    cursor = conn.cursor()

    with open(DATA_DIR / 'raions.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            oblast_id = cursor.execute(
                "SELECT id FROM oblasts WHERE name = ?",
                (row['oblast_name'],)
            ).fetchone()

            if oblast_id:
                cursor.execute(
                    "INSERT INTO raions (name, oblast_id, koatuu_code) VALUES (?, ?, ?)",
                    (row['name'], oblast_id[0], row['koatuu_code'])
                )

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM raions").fetchone()[0]
    print(f"Імпортовано {count} районів")


def import_settlements(conn):
    """Імпортує дані про населені пункти"""
    print("Імпорт населених пунктів...")
    cursor = conn.cursor()

    # Основні населені пункти
    with open(DATA_DIR / 'settlements.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            oblast_id = cursor.execute(
                "SELECT id FROM oblasts WHERE name = ?",
                (row['oblast_name'],)
            ).fetchone()

            if not oblast_id:
                continue

            raion_id = None
            if row['raion_name']:
                raion_result = cursor.execute(
                    "SELECT id FROM raions WHERE name = ? AND oblast_id = ?",
                    (row['raion_name'], oblast_id[0])
                ).fetchone()
                if raion_result:
                    raion_id = raion_result[0]

            population = int(row['population']) if row['population'] else None
            cursor.execute(
                "INSERT INTO settlements (name, type, oblast_id, raion_id, koatuu_code, population) VALUES (?, ?, ?, ?, ?, ?)",
                (row['name'], row['type'], oblast_id[0], raion_id, row['koatuu_code'], population)
            )

    # Додаткові міста
    if (DATA_DIR / 'additional_cities.csv').exists():
        print("Імпорт додаткових міст...")
        with open(DATA_DIR / 'additional_cities.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                oblast_id = cursor.execute(
                    "SELECT id FROM oblasts WHERE name = ?",
                    (row['oblast_name'],)
                ).fetchone()

                if not oblast_id:
                    continue

                raion_id = None
                if row['raion_name']:
                    raion_result = cursor.execute(
                        "SELECT id FROM raions WHERE name = ? AND oblast_id = ?",
                        (row['raion_name'], oblast_id[0])
                    ).fetchone()
                    if raion_result:
                        raion_id = raion_result[0]

                # Перевірити чи не існує вже
                exists = cursor.execute(
                    "SELECT id FROM settlements WHERE name = ? AND oblast_id = ?",
                    (row['name'], oblast_id[0])
                ).fetchone()

                if not exists:
                    population = int(row['population']) if row['population'] else None
                    cursor.execute(
                        "INSERT INTO settlements (name, type, oblast_id, raion_id, koatuu_code, population) VALUES (?, ?, ?, ?, ?, ?)",
                        (row['name'], row['type'], oblast_id[0], raion_id, row['koatuu_code'], population)
                    )

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM settlements").fetchone()[0]
    print(f"Імпортовано {count} населених пунктів")


def import_settlement_aliases(conn):
    """Імпортує альтернативні назви населених пунктів"""
    if not (DATA_DIR / 'settlement_aliases.csv').exists():
        print("Файл з альтернативними назвами не знайдено, пропускаємо...")
        return

    print("Імпорт альтернативних назв населених пунктів...")
    cursor = conn.cursor()

    with open(DATA_DIR / 'settlement_aliases.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cursor.execute(
                    """INSERT INTO settlement_aliases (settlement_id, alias_name, alias_type, valid_from, valid_to, reason)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (row['settlement_id'], row['alias_name'], row['alias_type'],
                     row.get('valid_from'), row.get('valid_to'), row.get('reason', ''))
                )
            except sqlite3.IntegrityError:
                # Вже існує
                pass

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM settlement_aliases").fetchone()[0]
    print(f"Імпортовано {count} альтернативних назв")


def import_courts(conn):
    """Імпортує дані про суди"""
    print("Імпорт судів...")
    cursor = conn.cursor()

    with open(DATA_DIR / 'courts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                """INSERT INTO courts (name, full_name, type, address, phone, email, website, head_judge)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (row['name'], row['full_name'], row['type'], row['address'],
                 row['phone'], row['email'], row['website'], row['head_judge'])
            )

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM courts").fetchone()[0]
    print(f"Імпортовано {count} судів")


def import_displaced_courts(conn):
    """Імпортує дані про тимчасово переміщені суди"""
    if not (DATA_DIR / 'displaced_courts.csv').exists():
        print("Файл з переміщеними судами не знайдено, пропускаємо...")
        return

    print("Імпорт тимчасово переміщених судів...")
    cursor = conn.cursor()

    with open(DATA_DIR / 'displaced_courts.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Знайти або створити суд
            court_result = cursor.execute(
                "SELECT id FROM courts WHERE name = ?",
                (row['court_name'],)
            ).fetchone()

            if not court_result:
                # Створити новий запис суду
                cursor.execute(
                    """INSERT INTO courts (name, full_name, type, address)
                       VALUES (?, ?, ?, ?)""",
                    (row['court_name'], row['court_name'], 'міський', row.get('current_address', ''))
                )
                court_id = cursor.lastrowid
            else:
                court_id = court_result[0]

            # Знайти ID територій
            orig_oblast_id = cursor.execute("SELECT id FROM oblasts WHERE name = ?", (row['original_oblast'],)).fetchone()
            orig_oblast_id = orig_oblast_id[0] if orig_oblast_id else None

            orig_settlement_id = None
            if row.get('original_settlement'):
                orig_settlement_result = cursor.execute(
                    "SELECT id FROM settlements WHERE name = ?",
                    (row['original_settlement'],)
                ).fetchone()
                if orig_settlement_result:
                    orig_settlement_id = orig_settlement_result[0]

            curr_oblast_id = cursor.execute("SELECT id FROM oblasts WHERE name = ?", (row['current_oblast'],)).fetchone()
            curr_oblast_id = curr_oblast_id[0] if curr_oblast_id else None

            curr_settlement_id = None
            if row.get('current_settlement'):
                curr_settlement_result = cursor.execute(
                    "SELECT id FROM settlements WHERE name = ?",
                    (row['current_settlement'],)
                ).fetchone()
                if curr_settlement_result:
                    curr_settlement_id = curr_settlement_result[0]

            # Вставити запис про переміщення
            cursor.execute(
                """INSERT INTO displaced_courts
                   (court_id, original_oblast_id, original_settlement_id, original_address,
                    current_oblast_id, current_settlement_id, current_address,
                    displacement_date, reason, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (court_id, orig_oblast_id, orig_settlement_id, row.get('original_address'),
                 curr_oblast_id, curr_settlement_id, row.get('current_address'),
                 row.get('displacement_date'), row.get('reason'), row.get('status', 'тимчасово_переміщений'))
            )

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM displaced_courts").fetchone()[0]
    print(f"Імпортовано {count} записів про переміщені суди")


def import_jurisdiction(conn):
    """Імпортує дані про юрисдикції"""
    print("Імпорт юрисдикцій...")
    cursor = conn.cursor()

    with open(DATA_DIR / 'jurisdiction.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            court_id = cursor.execute(
                "SELECT id FROM courts WHERE name = ?",
                (row['court_name'],)
            ).fetchone()

            if not court_id:
                print(f"Попередження: Суд не знайдено: {row['court_name']}")
                continue

            oblast_id = None
            if row['oblast_name']:
                oblast_result = cursor.execute(
                    "SELECT id FROM oblasts WHERE name = ?",
                    (row['oblast_name'],)
                ).fetchone()
                if oblast_result:
                    oblast_id = oblast_result[0]

            raion_id = None
            if row['raion_name'] and oblast_id:
                raion_result = cursor.execute(
                    "SELECT id FROM raions WHERE name = ? AND oblast_id = ?",
                    (row['raion_name'], oblast_id)
                ).fetchone()
                if raion_result:
                    raion_id = raion_result[0]

            settlement_id = None
            if row['settlement_name'] and oblast_id:
                settlement_result = cursor.execute(
                    "SELECT id FROM settlements WHERE name = ? AND oblast_id = ?",
                    (row['settlement_name'], oblast_id)
                ).fetchone()
                if settlement_result:
                    settlement_id = settlement_result[0]

            cursor.execute(
                """INSERT INTO jurisdiction (court_id, oblast_id, raion_id, settlement_id, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (court_id[0], oblast_id, raion_id, settlement_id, row.get('notes', ''))
            )

    conn.commit()
    count = cursor.execute("SELECT COUNT(*) FROM jurisdiction").fetchone()[0]
    print(f"Імпортовано {count} записів юрисдикції")


def main():
    """Головна функція"""
    print("=" * 60)
    print("Імпорт РОЗШИРЕНИХ даних про адреси України та суди")
    print("=" * 60)

    # Видалити стару базу якщо існує
    if DB_PATH.exists():
        print(f"Видалення старої бази даних: {DB_PATH}")
        DB_PATH.unlink()

    # Створити нову базу
    conn = create_database()

    try:
        # Імпортувати дані
        import_oblasts(conn)
        import_raions(conn)
        import_settlements(conn)
        import_settlement_aliases(conn)
        import_courts(conn)
        import_displaced_courts(conn)
        import_jurisdiction(conn)

        print("=" * 60)
        print("Імпорт завершено успішно!")
        print(f"База даних: {DB_PATH}")
        print("=" * 60)

        # Показати статистику
        cursor = conn.cursor()
        stats = {
            'Області': cursor.execute("SELECT COUNT(*) FROM oblasts").fetchone()[0],
            'Райони': cursor.execute("SELECT COUNT(*) FROM raions").fetchone()[0],
            'Населені пункти': cursor.execute("SELECT COUNT(*) FROM settlements").fetchone()[0],
            'Альтернативні назви': cursor.execute("SELECT COUNT(*) FROM settlement_aliases").fetchone()[0],
            'Суди': cursor.execute("SELECT COUNT(*) FROM courts").fetchone()[0],
            'Переміщені суди': cursor.execute("SELECT COUNT(*) FROM displaced_courts").fetchone()[0],
            'Записи юрисдикції': cursor.execute("SELECT COUNT(*) FROM jurisdiction").fetchone()[0],
        }

        print("\nСтатистика бази даних:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        print("\n⚠️  Додаткова інформація:")
        print("  - Додано альтернативні (старі) назви міст")
        print("  - Додано тимчасово переміщені суди")
        print("  - Покриття міст значно розширене")

    except Exception as e:
        print(f"Помилка при імпорті: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
