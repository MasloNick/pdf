# Ukraine Address Database for Court Jurisdiction

Database system for determining local court jurisdiction by address in Ukraine.

[Українська версія README](README_UA.md)

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Import data into database:
```bash
python scripts/import_data.py
```

3. Run the web application:
```bash
python scripts/webapp.py
```

4. Open your browser at `http://localhost:5000`

## Features

- **Search court jurisdiction** by oblast/raion/settlement
- **Batch processing** of CSV files with addresses
- **Address normalization** functionality
- **SQLite database** with 26 oblasts, 120+ raions, 121+ courts
- **Complete jurisdiction mapping** for all local courts of first instance

## Database Structure

- `oblasts` - Ukrainian oblasts (regions)
- `raions` - Districts within oblasts
- `settlements` - Cities, towns, villages
- `courts` - Local courts of first instance
- `jurisdiction` - Mapping between territories and courts

## Documentation

See [README_UA.md](README_UA.md) for detailed documentation in Ukrainian.

## Example CSV Format

```csv
oblast,district,settlement
Київська область,Броварський район,Бровари
Львівська область,Львівський район,Львів
```

See `examples/sample_addresses.csv` for more examples.

## API Usage

```python
from scripts.database import find_court_by_jurisdiction

court = find_court_by_jurisdiction(
    oblast_name="Київська область",
    raion_name="Броварський район",
    settlement_name="Бровари"
)
```

## License

Public data from open sources about Ukrainian administrative divisions and courts.
