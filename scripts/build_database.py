import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

def create_tables(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS oblasts (
            code TEXT PRIMARY KEY,
            name_new TEXT,
            name_old TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS districts (
            code TEXT PRIMARY KEY,
            oblast_code TEXT,
            name_new TEXT,
            name_old TEXT,
            FOREIGN KEY(oblast_code) REFERENCES oblasts(code)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settlements (
            code TEXT PRIMARY KEY,
            old_district_code TEXT,
            new_district_code TEXT,
            name_new TEXT,
            name_old TEXT,
            FOREIGN KEY(old_district_code) REFERENCES districts(code),
            FOREIGN KEY(new_district_code) REFERENCES districts(code)
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS courts (
            id INTEGER PRIMARY KEY,
            oblast_code TEXT,
            district_code TEXT,
            settlement_code TEXT,
            name TEXT,
            address TEXT,
            FOREIGN KEY(oblast_code) REFERENCES oblasts(code),
            FOREIGN KEY(district_code) REFERENCES districts(code),
            FOREIGN KEY(settlement_code) REFERENCES settlements(code)
        )
    ''')
    conn.commit()

def load_csv(conn, table, path):
    cur = conn.cursor()
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [tuple(row[col] for col in reader.fieldnames) for row in reader]
    placeholders = ', '.join('?' * len(reader.fieldnames))
    cur.executemany(
        f'INSERT INTO {table} ({", ".join(reader.fieldnames)}) VALUES ({placeholders})',
        rows
    )
    conn.commit()

def build_db(db_path='admin_units.db'):
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    load_csv(conn, 'oblasts', DATA_DIR / 'oblasts.csv')
    load_csv(conn, 'districts', DATA_DIR / 'districts.csv')
    load_csv(conn, 'settlements', DATA_DIR / 'settlements.csv')
    load_csv(conn, 'courts', DATA_DIR / 'courts.csv')
    conn.close()

if __name__ == '__main__':
    build_db()
