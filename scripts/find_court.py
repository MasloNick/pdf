import sqlite3
from argparse import ArgumentParser


def find_court(db_path, oblast, district, settlement):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    query = """
        SELECT c.name, c.address
        FROM courts c
        JOIN oblasts o ON c.oblast_code = o.code
        JOIN districts d ON c.district_code = d.code
        JOIN settlements s ON c.settlement_code = s.code
        WHERE (o.name_new = ? OR o.name_old = ?)
          AND (d.name_new = ? OR d.name_old = ?)
          AND (s.name_new = ? OR s.name_old = ?)
    """
    cur.execute(query, (oblast, oblast, district, district, settlement, settlement))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None


def main():
    parser = ArgumentParser(description="Find court by address")
    parser.add_argument('--db', default='admin_units.db')
    parser.add_argument('--oblast', required=True, help='Oblast name (old or new)')
    parser.add_argument('--district', required=True, help='District name (old or new)')
    parser.add_argument('--settlement', required=True, help='Settlement name (old or new)')
    args = parser.parse_args()

    name, address = find_court(args.db, args.oblast, args.district, args.settlement)
    if name:
        print(f"{name} ({address})")
    else:
        print("Court not found")


if __name__ == '__main__':
    main()
