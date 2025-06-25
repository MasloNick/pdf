# Ukrainian Court Jurisdiction Demo

This repository contains a small demonstration of how to build a database of Ukrainian administrative units with both old and new names. It shows a simplified approach for linking oblasts, districts, settlements and courts so that a search by either old or new address can locate the relevant court.

The data in `data/` is just sample information. To build a real database you should download official open datasets such as the **Кодифікатор адміністративно-територіальних одиниць та територій територіальних громад (КАТОТТГ)** and lists of postal addresses. Place the CSV files in the `data/` directory using the same column structure as the examples.

## Building the database

Run the script below to create `admin_units.db` from the CSV files:

```bash
python scripts/build_database.py
```

## Searching for a court

Use `find_court.py` to find a court by oblast, district and settlement name (old or new):

```bash
python scripts/find_court.py --oblast "Дніпропетровська область" --district "Дніпровський район" --settlement "Дніпро"
```

The script will print the court name and address if found.
