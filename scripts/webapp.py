from flask import Flask, flash, jsonify, request, render_template, send_file, redirect, url_for
import csv
import io
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if __package__ in (None, ""):
    sys.path.append(str(ROOT_DIR))

app = Flask(__name__, template_folder=str(ROOT_DIR / "templates"))
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

from scripts.collect_official_sources import (  # noqa: E402,E401
    ADMINISTRATIVE_HIERARCHY,
    OFFICIAL_SOURCES,
    DecisionRegistry,
    OfficialSourceCollector,
)
from scripts.models import init_db, get_db, AuctionRecord, get_all_auctions  # noqa: E402
from scripts.analysis.portfolio import (  # noqa: E402
    analyze_portfolio,
    analyze_auction,
    import_portfolio_csv,
)
from scripts.analysis.pricing import recommend_price, compare_price_to_market  # noqa: E402
from scripts.scrapers.banks import (  # noqa: E402
    BANK_REGISTRY,
    AUCTION_PLATFORMS,
    SEARCH_STRATEGIES,
    get_accreditation_info,
)


# Initialise database on import
init_db()


# ============================================================================
# Helpers
# ============================================================================

def normalize(text: str) -> str:
    """Normalise Ukrainian address text.

    Python's ``str.title()`` treats the apostrophe as a word boundary so
    ``"об'єднана".title()`` produces ``"Об'Єднана"`` instead of the
    correct ``"Об'єднана"``.  This function capitalises only the first
    letter of every *space-separated* word, which is safe for Ukrainian.
    """
    if not text:
        return ""
    text = " ".join(text.strip().split())
    words = text.split()
    return " ".join(
        word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
        for word in words
    )


def resolve_code(oblast: str, district: str, settlement: str) -> str:
    """Return a code built from address components."""
    parts = [p.strip() for p in (oblast, district, settlement) if p and p.strip()]
    return "-".join(parts)


def find_court(code: str) -> str:
    """Dummy lookup of court by code."""
    return f"Court for {code}"


def process_file(rows: List[Dict[str, str]], normalise: bool = False) -> List[Dict[str, str]]:
    """Process list of address dictionaries and append court info."""
    processed = []
    for row in rows:
        oblast = row.get("oblast", "")
        district = row.get("district", "")
        settlement = row.get("settlement", "")
        if normalise:
            oblast = normalize(oblast)
            district = normalize(district)
            settlement = normalize(settlement)
        code = resolve_code(oblast, district, settlement)
        court = find_court(code)
        processed.append({
            "oblast": oblast,
            "district": district,
            "settlement": settlement,
            "court": court,
        })
    return processed


def _fmt_uah(val: Any) -> str:
    """Format a number as UAH currency string."""
    if val is None:
        return "—"
    try:
        return f"{float(val):,.2f} грн".replace(",", " ")
    except (ValueError, TypeError):
        return "—"


# Register template helpers
app.jinja_env.globals["fmt_uah"] = _fmt_uah


# ============================================================================
# Dashboard — main page
# ============================================================================

@app.route("/")
def dashboard():
    with get_db() as conn:
        auctions = get_all_auctions(conn, limit=50)

    stats = {
        "total_auctions": len(auctions),
        "active": sum(1 for a in auctions if a.get("status") == "active"),
        "total_debt": sum(a.get("total_debt") or 0 for a in auctions),
        "banks_tracked": len(BANK_REGISTRY),
    }
    return render_template("dashboard.html", stats=stats, auctions=auctions[:20])


# ============================================================================
# Portfolio analysis
# ============================================================================

@app.route("/portfolio", methods=["GET", "POST"])
def portfolio_analysis():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Будь ласка, оберіть CSV-файл з даними портфеля.")
            return redirect(url_for("portfolio_analysis"))
        try:
            csv_text = file.stream.read().decode("utf-8")
        except UnicodeDecodeError:
            flash("Не вдалося прочитати файл. Переконайтесь, що він у кодуванні UTF-8.")
            return redirect(url_for("portfolio_analysis"))

        records, warnings = import_portfolio_csv(csv_text)
        for w in warnings:
            flash(w)
        if not records:
            flash("Не вдалося розпізнати дані портфеля.")
            return redirect(url_for("portfolio_analysis"))

        summary = analyze_portfolio(records)

        # Pricing recommendation
        pricing = recommend_price(
            total_debt=summary.total_debt,
            portfolio_type="physical" if summary.physical_count > summary.legal_count else "legal",
            principal_ratio=summary.principal_ratio,
            num_debtors=summary.total_records,
            avg_debt=summary.avg_debt,
        )

        return render_template(
            "portfolio_result.html",
            summary=summary.to_dict(),
            pricing=pricing.to_dict(),
            records=records[:100],  # Show first 100 for preview
            total_records=len(records),
        )

    return render_template("portfolio.html")


# ============================================================================
# Auction search / scraping
# ============================================================================

@app.route("/auctions")
def auctions_list():
    source = request.args.get("source", "")
    with get_db() as conn:
        auctions = get_all_auctions(conn, source=source or None, limit=200)
    return render_template("auctions.html", auctions=auctions, current_source=source)


@app.route("/auctions/scan")
def auctions_scan():
    """Run scrapers and show results (does NOT require live internet for UI)."""
    results: Dict[str, Any] = {"setam": [], "prozorro": [], "dgf": [], "banks": [], "errors": []}

    # Try SETAM
    try:
        from scripts.scrapers.setam import SetamScraper
        scraper = SetamScraper(timeout=15, max_retries=2)
        raw_items = scraper.search_npl(per_page=20)
        for raw in raw_items:
            parsed = scraper.parse_lot(raw)
            results["setam"].append(parsed)
            # Save to DB
            with get_db() as conn:
                AuctionRecord(**{k: v for k, v in parsed.items() if k != "raw_data"}).save(conn)
        results["errors"].extend(scraper.errors)
    except Exception as exc:
        results["errors"].append(f"SETAM: {exc}")

    # Try ProZorro
    try:
        from scripts.scrapers.prozorro import ProzorroScraper
        scraper = ProzorroScraper(timeout=15, max_retries=2)
        raw_items = scraper.search_npl(limit=20)
        for raw in raw_items:
            parsed = scraper.parse_procedure(raw)
            results["prozorro"].append(parsed)
            with get_db() as conn:
                AuctionRecord(**{k: v for k, v in parsed.items() if k != "raw_data"}).save(conn)
        results["errors"].extend(scraper.errors)
    except Exception as exc:
        results["errors"].append(f"ProZorro: {exc}")

    # Try DGF
    try:
        from scripts.scrapers.prozorro import DGFScraper
        scraper = DGFScraper(timeout=15, max_retries=2)
        dgf_items = scraper.search_dgf_sales()
        results["dgf"] = dgf_items
        results["errors"].extend(scraper.errors)
    except Exception as exc:
        results["errors"].append(f"DGF: {exc}")

    # Try bank websites
    try:
        from scripts.scrapers.banks import BankSiteScraper
        scraper = BankSiteScraper(timeout=10, max_retries=1)
        bank_items = scraper.scan_all_banks()
        results["banks"] = bank_items
        results["errors"].extend(scraper.errors)
    except Exception as exc:
        results["errors"].append(f"Banks: {exc}")

    total_found = sum(len(v) for k, v in results.items() if k != "errors")
    flash(f"Сканування завершено. Знайдено {total_found} результатів.")

    return render_template("scan_results.html", results=results)


# ============================================================================
# Pricing calculator
# ============================================================================

@app.route("/pricing", methods=["GET", "POST"])
def pricing():
    recommendation = None
    comparison = None

    if request.method == "POST":
        total_debt = float(request.form.get("total_debt", 0) or 0)
        portfolio_type = request.form.get("portfolio_type", "physical")
        debt_category = request.form.get("debt_category", "seasoned")
        principal_ratio = float(request.form.get("principal_ratio", 50) or 50) / 100
        num_debtors = int(request.form.get("num_debtors", 100) or 100)
        avg_debt = float(request.form.get("avg_debt", 0) or 0)
        seller_type = request.form.get("seller_type", "bank")
        documentation = request.form.get("documentation", "partial")
        asking_price = float(request.form.get("asking_price", 0) or 0)

        if avg_debt == 0 and num_debtors > 0:
            avg_debt = total_debt / num_debtors

        recommendation = recommend_price(
            total_debt=total_debt,
            portfolio_type=portfolio_type,
            debt_category=debt_category,
            principal_ratio=principal_ratio,
            num_debtors=num_debtors,
            avg_debt=avg_debt,
            seller_type=seller_type,
            documentation=documentation,
        ).to_dict()

        if asking_price > 0:
            comparison = compare_price_to_market(
                asking_price=asking_price,
                total_debt=total_debt,
                portfolio_type=portfolio_type,
                debt_category=debt_category,
            )

    return render_template("pricing.html", recommendation=recommendation, comparison=comparison)


# ============================================================================
# Company checker
# ============================================================================

@app.route("/check-company", methods=["GET", "POST"])
def check_company():
    result = None
    if request.method == "POST":
        edrpou = request.form.get("edrpou", "").strip()
        name = request.form.get("name", "").strip()
        if not edrpou:
            flash("Введіть код ЄДРПОУ.")
            return redirect(url_for("check_company"))
        try:
            from scripts.checkers.company import CompanyChecker
            checker = CompanyChecker(timeout=15, max_retries=2)
            result = checker.check_company(edrpou, name).to_dict()
        except Exception as exc:
            flash(f"Помилка перевірки: {exc}")

    return render_template("check_company.html", result=result)


# ============================================================================
# Monitoring / Sources tracking
# ============================================================================

@app.route("/monitoring")
def monitoring():
    accreditation = get_accreditation_info()
    return render_template(
        "monitoring.html",
        banks=BANK_REGISTRY,
        platforms=AUCTION_PLATFORMS,
        strategies=SEARCH_STRATEGIES,
        accreditation=accreditation,
    )


# ============================================================================
# Original routes (kept for backward compatibility)
# ============================================================================

@app.route("/address-search", methods=["GET", "POST"])
def address_search():
    if request.method == "POST":
        oblast = request.form.get("oblast", "").strip()
        district = request.form.get("district", "").strip()
        settlement = request.form.get("settlement", "").strip()
        if not any((oblast, district, settlement)):
            flash("Введіть хоча б одне поле адреси.")
            return redirect(url_for("address_search"))
        normalise = bool(request.form.get("normalise"))
        if normalise:
            oblast = normalize(oblast)
            district = normalize(district)
            settlement = normalize(settlement)
        code = resolve_code(oblast, district, settlement)
        court = find_court(code)
        return render_template(
            "result.html",
            result=court,
            oblast=oblast,
            district=district,
            settlement=settlement,
        )
    return render_template("index.html")


@app.route("/batch", methods=["GET", "POST"])
def batch():
    if request.method == "POST":
        file = request.files.get("file")
        normalise = bool(request.form.get("normalise"))
        if not file or not file.filename:
            flash("Будь ласка, оберіть CSV-файл.")
            return redirect(url_for("batch"))
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
        except UnicodeDecodeError:
            flash("Не вдалося прочитати файл. Переконайтесь, що він у кодуванні UTF-8.")
            return redirect(url_for("batch"))
        reader = csv.DictReader(stream)
        rows = list(reader)
        if not rows:
            flash("Файл порожній або не містить даних.")
            return redirect(url_for("batch"))
        processed = process_file(rows, normalise=normalise)
        return render_template("batch_result.html", rows=processed)
    return render_template("batch.html")


@app.route("/official-sources")
def official_sources():
    download = request.args.get("download")
    collector = OfficialSourceCollector(OFFICIAL_SOURCES)
    registry = collector.collect(DecisionRegistry())

    if download == "csv":
        output = io.StringIO()
        registry.to_csv(output)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="official_decisions.csv",
        )

    if download == "json":
        output = io.StringIO()
        registry.to_json(output, ensure_ascii=False)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="application/json",
            as_attachment=True,
            download_name="official_decisions.json",
        )

    return render_template(
        "official_sources.html",
        hierarchy=ADMINISTRATIVE_HIERARCHY,
        registry=registry.to_dict(),
        errors=registry.errors,
        sources=OFFICIAL_SOURCES,
    )


@app.route("/normalize", methods=["GET", "POST"])
def normalize_route():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Будь ласка, оберіть CSV-файл.")
            return redirect(url_for("normalize_route"))
        try:
            stream = io.StringIO(file.stream.read().decode("utf-8"))
        except UnicodeDecodeError:
            flash("Не вдалося прочитати файл. Переконайтесь, що він у кодуванні UTF-8.")
            return redirect(url_for("normalize_route"))
        reader = csv.DictReader(stream)
        rows = list(reader)
        if not rows or not reader.fieldnames:
            flash("Файл порожній або не містить даних.")
            return redirect(url_for("normalize_route"))
        for row in rows:
            for key in row:
                row[key] = normalize(row[key] or "")
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="normalized.csv",
        )
    return render_template("normalize.html")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
