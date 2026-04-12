from flask import Flask, flash, request, render_template, send_file, redirect, url_for
import csv
import io
import os
from pathlib import Path
import sys
from typing import List, Dict

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


def normalize(text: str) -> str:
    """Normalise Ukrainian address text.

    Python's ``str.title()`` treats the apostrophe as a word boundary so
    ``"об'єднана".title()`` produces ``"Об'Єднана"`` instead of the
    correct ``"Об'єднана"``.  This function capitalises only the first
    letter of every *space-separated* word, which is safe for Ukrainian.
    """
    if not text:
        return ""
    text = " ".join(text.strip().split())          # collapse whitespace
    words = text.split()
    return " ".join(
        word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper()
        for word in words
    )


def resolve_code(oblast: str, district: str, settlement: str) -> str:
    """Return a code built from address components.

    The caller is responsible for normalising the values beforehand.
    This function only joins the non-empty parts with a hyphen.
    """
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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        oblast = request.form.get("oblast", "").strip()
        district = request.form.get("district", "").strip()
        settlement = request.form.get("settlement", "").strip()
        if not any((oblast, district, settlement)):
            flash("Введіть хоча б одне поле адреси.")
            return redirect(url_for("index"))
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
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode("utf-8")),
            mimetype="text/csv",
            as_attachment=True,
            download_name="official_decisions.csv",
        )

    if download == "json":
        output = io.StringIO()
        registry.to_json(output, ensure_ascii=False)
        output.seek(0)
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
