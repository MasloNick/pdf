from flask import Flask, request, render_template, send_file, redirect, url_for
import csv
import io
from pathlib import Path
import sys
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if __package__ in (None, ""):
    sys.path.append(str(ROOT_DIR))

app = Flask(__name__, template_folder=str(ROOT_DIR / "templates"))

from scripts.collect_official_sources import (  # noqa: E402,E401
    ADMINISTRATIVE_HIERARCHY,
    OFFICIAL_SOURCES,
    DecisionRegistry,
    OfficialSourceCollector,
)


def normalize(text: str) -> str:
    """Very basic normalisation for demonstration."""
    return " ".join(text.strip().title().split())


def resolve_code(oblast: str, district: str, settlement: str) -> str:
    """Return a dummy code built from components."""
    parts = [normalize(p) for p in (oblast, district, settlement) if p]
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
        oblast = request.form.get("oblast", "")
        district = request.form.get("district", "")
        settlement = request.form.get("settlement", "")
        normalise = bool(request.form.get("normalise"))
        if normalise:
            oblast = normalize(oblast)
            district = normalize(district)
            settlement = normalize(settlement)
        code = resolve_code(oblast, district, settlement)
        court = find_court(code)
        return render_template("result.html", result=court)
    return render_template("index.html")


@app.route("/batch", methods=["GET", "POST"])
def batch():
    if request.method == "POST":
        file = request.files.get("file")
        normalise = bool(request.form.get("normalise"))
        if not file:
            return redirect(url_for("batch"))
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        rows = list(reader)
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
        if not file:
            return redirect(url_for("normalize_route"))
        stream = io.StringIO(file.stream.read().decode("utf-8"))
        reader = csv.DictReader(stream)
        rows = list(reader)
        for row in rows:
            for key in row:
                row[key] = normalize(row[key])
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        output.seek(0)
        return send_file(io.BytesIO(output.read().encode("utf-8")),
                         mimetype="text/csv",
                         as_attachment=True,
                         download_name="normalized.csv")
    return render_template("normalize.html")


if __name__ == "__main__":
    app.run(debug=True)
