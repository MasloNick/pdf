"""Celery tasks for portfolio import."""

import os
from celery import shared_task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.import_service import ImportService
from app.models.debtor import Debtor
from app.models.portfolio import Portfolio

engine = create_engine(settings.DATABASE_URL_SYNC)


@shared_task(bind=True, name="import.process_portfolio")
def process_import_task(self, file_path: str, config: dict):
    """
    Background task: import debtors from file.
    Reports progress via Celery state updates.
    """
    service = ImportService()
    ext = os.path.splitext(file_path)[1].lower()

    df = service.parse_file(file_path, ext)
    total = len(df)
    added = 0
    updated = 0
    skipped = 0
    errors = []

    # Column mappings
    mappings = {}
    for m in config.get("column_mappings", []):
        mappings[m["target_field"]] = m["source_column"]

    # Get or create portfolio
    mode = config.get("mode", "new")

    with Session(engine) as session:
        portfolio_id = config.get("portfolio_id")
        if mode == "new" and not portfolio_id:
            portfolio = Portfolio(name=config.get("portfolio_name", "Imported Portfolio"))
            session.add(portfolio)
            session.commit()
            portfolio_id = portfolio.id

        for idx, row in df.iterrows():
            try:
                debtor_data = {}
                for target_field, source_col in mappings.items():
                    if source_col in row and row[source_col] is not None:
                        val = row[source_col]
                        if hasattr(val, "item"):
                            val = val.item()
                        if isinstance(val, float) and val != val:  # NaN check
                            val = None
                        debtor_data[target_field] = val

                if not debtor_data.get("full_name"):
                    skipped += 1
                    errors.append({"row": idx + 2, "error": "Missing full_name"})
                    continue

                # Validate IPN if present
                ipn = debtor_data.get("ipn")
                if ipn:
                    ipn = str(ipn).strip()
                    if not service.validate_ipn(ipn):
                        errors.append({"row": idx + 2, "error": f"Invalid IPN: {ipn}"})
                        debtor_data["ipn"] = None

                # Check for duplicate
                if ipn and mode != "new":
                    existing = session.query(Debtor).filter(
                        Debtor.ipn == ipn,
                        Debtor.portfolio_id == portfolio_id,
                    ).first()
                    if existing and mode == "update":
                        for k, v in debtor_data.items():
                            if v is not None:
                                setattr(existing, k, v)
                        updated += 1
                        continue
                    elif existing:
                        skipped += 1
                        continue

                debtor = Debtor(portfolio_id=portfolio_id, **debtor_data)
                session.add(debtor)
                added += 1

                # Report progress every 100 rows
                if (idx + 1) % 100 == 0:
                    session.commit()
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "total": total,
                            "processed": idx + 1,
                            "added": added,
                            "updated": updated,
                            "skipped": skipped,
                        },
                    )

            except Exception as e:
                skipped += 1
                errors.append({"row": idx + 2, "error": str(e)})

        session.commit()

    # Clean up uploaded file
    try:
        os.remove(file_path)
    except OSError:
        pass

    return {
        "total_rows": total,
        "processed": total,
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "errors": errors[:100],  # Limit error list
    }
