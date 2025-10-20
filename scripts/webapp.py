from flask import Flask, request, render_template, send_file, redirect, url_for
import csv
import io
from typing import List, Dict, Optional
import sys
from pathlib import Path

# Додати шлях до модуля database
sys.path.insert(0, str(Path(__file__).parent))

from database import (
    find_court_by_jurisdiction,
    normalize_text,
    search_settlements,
    get_all_oblasts,
    DB_PATH
)

app = Flask(__name__)


def normalize(text: str) -> str:
    """Нормалізація тексту для сумісності зі старим кодом."""
    return " ".join(text.strip().title().split())


def find_court_info(oblast: str, district: str, settlement: str) -> Optional[Dict]:
    """
    Знаходить суд за адресою

    Returns:
        Словник з інформацією про суд або None
    """
    court = find_court_by_jurisdiction(
        oblast_name=oblast if oblast else None,
        raion_name=district if district else None,
        settlement_name=settlement if settlement else None
    )
    return court


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

        # Знайти суд за адресою
        court_info = find_court_info(oblast, district, settlement)

        if court_info:
            court_text = f"{court_info['name']}"
            if court_info.get('address'):
                court_text += f" (адреса: {court_info['address']})"
            if court_info.get('phone'):
                court_text += f", тел: {court_info['phone']}"
        else:
            court_text = "Суд не знайдено"

        processed.append({
            "oblast": oblast,
            "district": district,
            "settlement": settlement,
            "court": court_text,
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

        # Знайти суд за адресою
        court_info = find_court_info(oblast, district, settlement)

        if court_info:
            result = {
                'name': court_info['name'],
                'full_name': court_info.get('full_name', ''),
                'type': court_info.get('type', ''),
                'address': court_info.get('address', ''),
                'phone': court_info.get('phone', ''),
                'email': court_info.get('email', ''),
                'website': court_info.get('website', ''),
            }
        else:
            result = None

        return render_template("result.html", result=result,
                             search_params={'oblast': oblast, 'district': district, 'settlement': settlement})

    # Перевірити чи існує база даних
    db_exists = DB_PATH.exists()
    return render_template("index.html", db_exists=db_exists)


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
