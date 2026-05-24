"""CourtNinja — Судовий Ніндзя v2.1

Professional CRM web application for working with Ukrainian courts.
Features: auth, court search, case management, fee calculator, document generator,
deadline tracker, official sources collector.
"""

from flask import Flask, request, render_template, send_file, redirect, url_for, flash, session
import csv
import io
import json
from pathlib import Path
import sys
from typing import List, Dict

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

if __package__ in (None, ""):
    sys.path.append(str(ROOT_DIR))

app = Flask(__name__, template_folder=str(ROOT_DIR / "templates"))
app.secret_key = "court-ninja-secret-key-change-in-production"

from scripts.collect_official_sources import (  # noqa: E402,E401
    ADMINISTRATIVE_HIERARCHY,
    OFFICIAL_SOURCES,
    DecisionRegistry,
    OfficialSourceCollector,
)
from scripts.court_database import CourtDatabase, COURT_TYPES  # noqa: E402
from scripts.case_manager import CaseManager, CASE_TYPES, CASE_STATUSES  # noqa: E402
from scripts.fee_calculator import (  # noqa: E402
    calculate_fee,
    get_fee_options,
    FEE_CATEGORIES,
    PROCEDURAL_DEADLINES,
)
from scripts.document_generator import (  # noqa: E402
    DOCUMENT_TYPES,
    generate_claim,
    generate_response,
    generate_appeal,
    generate_motion,
    generate_court_order_application,
)
from scripts.auth import UserManager, ROLES, login_required, role_required  # noqa: E402

court_db = CourtDatabase()
case_mgr = CaseManager()
user_mgr = UserManager()


def current_user_id() -> str:
    return session.get("user_id", "")


@app.context_processor
def inject_user():
    user = None
    if "user_id" in session:
        user = user_mgr.get_user(session["user_id"])
    return dict(current_user=user, roles=ROLES)


def normalize(text: str) -> str:
    return " ".join(text.strip().title().split())


def resolve_code(oblast: str, district: str, settlement: str) -> str:
    parts = [normalize(p) for p in (oblast, district, settlement) if p]
    return "-".join(parts)


def find_court(code: str) -> str:
    parts = code.split("-")
    settlement = parts[-1] if parts else code
    results = court_db.find_by_settlement(settlement)
    if results:
        return results[0].name
    return f"Суд для {code} (потрібно уточнити)"


def process_file(rows: List[Dict[str, str]], normalise: bool = False) -> List[Dict[str, str]]:
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


# ============================================================
# Auth
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = user_mgr.authenticate(email, password)
        if user:
            session["user_id"] = user.id
            session["user_role"] = user.role
            session["user_name"] = user.username
            flash(f"Ласкаво просимо, {user.username}!", "success")
            return redirect(url_for("index"))
        flash("Невірний email або пароль", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "advocate")
        if len(password) < 6:
            flash("Пароль має бути не менше 6 символів", "danger")
            return render_template("register.html")
        user = user_mgr.register(username, email, password, role)
        if not user:
            flash("Користувач з таким email вже існує", "danger")
            return render_template("register.html")
        session["user_id"] = user.id
        session["user_role"] = user.role
        session["user_name"] = user.username
        flash("Реєстрація успішна!", "success")
        return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Ви вийшли з системи", "info")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    user = user_mgr.get_user(current_user_id())
    return render_template("profile.html", user=user, roles=ROLES)


# ============================================================
# Dashboard
# ============================================================

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    uid = current_user_id()
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

    upcoming = case_mgr.get_upcoming_deadlines(days=14, user_id=uid)
    overdue = [d for d in upcoming if d.get("is_overdue")]
    stats = case_mgr.stats(user_id=uid)

    return render_template(
        "index.html",
        court_count=len(court_db.courts),
        case_count=stats.get("total", 0),
        deadline_count=len(upcoming),
        overdue_count=len(overdue),
        upcoming_deadlines=upcoming,
        stats=stats,
    )


# ============================================================
# Courts
# ============================================================

@app.route("/courts")
@login_required
def courts():
    query = request.args.get("q", "")
    oblast = request.args.get("oblast", "")
    court_type = request.args.get("court_type", "")

    results = court_db.search(query=query, oblast=oblast, court_type=court_type)

    return render_template(
        "courts.html",
        courts=results,
        query=query,
        oblast=oblast,
        selected_type=court_type,
        oblasts=court_db.get_oblasts(),
        court_types=COURT_TYPES,
    )


# ============================================================
# Cases
# ============================================================

@app.route("/cases")
@login_required
def cases():
    uid = current_user_id()
    query = request.args.get("q", "")
    status = request.args.get("status", "")
    case_type = request.args.get("case_type", "")

    results = case_mgr.list_cases(status=status, case_type=case_type, query=query, user_id=uid)

    return render_template(
        "cases.html",
        cases=results,
        query=query,
        selected_status=status,
        selected_type=case_type,
        statuses=CASE_STATUSES,
        case_types=CASE_TYPES,
    )


@app.route("/cases/new", methods=["GET", "POST"])
@login_required
@role_required("advocate", "assistant")
def case_new():
    if request.method == "POST":
        court_id = request.form.get("court_id", "")
        court = court_db.find_by_id(court_id)
        court_name = court.name if court else "Невідомий суд"

        case = case_mgr.create_case(
            case_number=request.form.get("case_number", ""),
            title=request.form.get("title", ""),
            case_type=request.form.get("case_type", "civil"),
            court_id=court_id,
            court_name=court_name,
            description=request.form.get("description", ""),
            judge=request.form.get("judge", ""),
            user_id=current_user_id(),
        )
        flash("Справу створено!", "success")
        return redirect(url_for("case_detail", case_id=case.id))

    return render_template(
        "case_form.html",
        case=None,
        case_types=CASE_TYPES,
        statuses=CASE_STATUSES,
        courts=court_db.courts,
    )


@app.route("/cases/<case_id>")
@login_required
def case_detail(case_id):
    case = case_mgr.get_case(case_id)
    if not case or (case.user_id and case.user_id != current_user_id()):
        flash("Справу не знайдено", "danger")
        return redirect(url_for("cases"))

    return render_template(
        "case_detail.html",
        case=case,
        case_types=CASE_TYPES,
        statuses=CASE_STATUSES,
    )


@app.route("/cases/<case_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("advocate", "assistant")
def case_edit(case_id):
    case = case_mgr.get_case(case_id)
    if not case or (case.user_id and case.user_id != current_user_id()):
        flash("Справу не знайдено", "danger")
        return redirect(url_for("cases"))

    if request.method == "POST":
        court_id = request.form.get("court_id", case.court_id)
        court = court_db.find_by_id(court_id)
        court_name = court.name if court else case.court_name

        case_mgr.update_case(
            case_id,
            case_number=request.form.get("case_number", case.case_number),
            title=request.form.get("title", case.title),
            case_type=request.form.get("case_type", case.case_type),
            court_id=court_id,
            court_name=court_name,
            status=request.form.get("status", case.status),
            description=request.form.get("description", case.description),
            judge=request.form.get("judge", case.judge),
            next_hearing=request.form.get("next_hearing", case.next_hearing),
        )
        flash("Справу оновлено!", "success")
        return redirect(url_for("case_detail", case_id=case_id))

    return render_template(
        "case_form.html",
        case=case,
        case_types=CASE_TYPES,
        statuses=CASE_STATUSES,
        courts=court_db.courts,
    )


@app.route("/cases/<case_id>/delete", methods=["POST"])
@login_required
@role_required("advocate")
def case_delete(case_id):
    case = case_mgr.get_case(case_id)
    if case and case.user_id and case.user_id != current_user_id():
        flash("Немає прав для видалення", "danger")
        return redirect(url_for("cases"))
    case_mgr.delete_case(case_id)
    flash("Справу видалено", "success")
    return redirect(url_for("cases"))


@app.route("/cases/<case_id>/party", methods=["POST"])
@login_required
@role_required("advocate", "assistant")
def case_add_party(case_id):
    party = {
        "name": request.form.get("name", ""),
        "role": request.form.get("role", ""),
        "address": request.form.get("address", ""),
    }
    case_mgr.add_party(case_id, party)
    flash("Сторону додано", "success")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/cases/<case_id>/deadline", methods=["POST"])
@login_required
@role_required("advocate", "assistant")
def case_add_deadline(case_id):
    case_mgr.add_deadline(
        case_id,
        title=request.form.get("title", ""),
        due_date=request.form.get("due_date", ""),
        description=request.form.get("description", ""),
    )
    flash("Дедлайн додано", "success")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/cases/<case_id>/deadline/<deadline_id>/complete", methods=["POST"])
@login_required
def case_complete_deadline(case_id, deadline_id):
    case_mgr.complete_deadline(case_id, deadline_id)
    flash("Дедлайн завершено", "success")
    return redirect(url_for("case_detail", case_id=case_id))


@app.route("/cases/<case_id>/note", methods=["POST"])
@login_required
def case_add_note(case_id):
    case_mgr.add_note(case_id, text=request.form.get("text", ""), author=session.get("user_name", "user"))
    flash("Нотатку додано", "success")
    return redirect(url_for("case_detail", case_id=case_id))


# ============================================================
# Deadlines
# ============================================================

@app.route("/deadlines")
@login_required
def deadlines():
    uid = current_user_id()
    all_deadlines = case_mgr.get_upcoming_deadlines(days=30, user_id=uid)
    overdue = [d for d in all_deadlines if d.get("is_overdue")]

    return render_template(
        "deadlines.html",
        deadlines=all_deadlines,
        overdue_deadlines=overdue,
    )


# ============================================================
# Fee Calculator
# ============================================================

@app.route("/calculator", methods=["GET", "POST"])
@login_required
def calculator():
    selected_category = request.form.get("category", request.args.get("category", "civil"))
    selected_index = 0
    claim_amount = 0.0
    result = None

    fee_options = get_fee_options(selected_category)

    if request.method == "POST":
        try:
            selected_index = int(request.form.get("fee_index", 0))
        except (ValueError, TypeError):
            selected_index = 0
        try:
            claim_amount = float(request.form.get("claim_amount", 0))
        except (ValueError, TypeError):
            claim_amount = 0.0

        result = calculate_fee(selected_category, selected_index, claim_amount)

    return render_template(
        "calculator.html",
        categories=FEE_CATEGORIES,
        selected_category=selected_category,
        fee_options=fee_options,
        selected_index=selected_index,
        claim_amount=claim_amount,
        result=result,
        deadlines=PROCEDURAL_DEADLINES,
    )


# ============================================================
# Document Generator
# ============================================================

@app.route("/documents", methods=["GET"])
@login_required
def documents():
    doc_type = request.args.get("type", "")
    return render_template(
        "documents.html",
        doc_types=DOCUMENT_TYPES,
        doc_type=doc_type,
        generated_doc=None,
    )


@app.route("/documents/generate", methods=["POST"])
@login_required
def documents_generate():
    doc_type = request.form.get("doc_type", "")
    generated = ""

    if doc_type == "claim":
        claim_amount = 0.0
        try:
            claim_amount = float(request.form.get("claim_amount", 0))
        except (ValueError, TypeError):
            pass
        generated = generate_claim(
            court_name=request.form.get("court_name", ""),
            plaintiff=request.form.get("plaintiff", ""),
            plaintiff_address=request.form.get("plaintiff_address", ""),
            defendant=request.form.get("defendant", ""),
            defendant_address=request.form.get("defendant_address", ""),
            subject=request.form.get("subject", ""),
            circumstances=request.form.get("circumstances", ""),
            legal_basis=request.form.get("legal_basis", ""),
            claim_amount=claim_amount,
            demands=request.form.get("demands", ""),
            attachments=request.form.get("attachments", ""),
        )
    elif doc_type == "response":
        generated = generate_response(
            court_name=request.form.get("court_name", ""),
            case_number=request.form.get("case_number", ""),
            defendant=request.form.get("defendant", ""),
            defendant_address=request.form.get("defendant_address", ""),
            plaintiff=request.form.get("plaintiff", ""),
            objections=request.form.get("objections", ""),
            legal_basis=request.form.get("legal_basis", ""),
            demands=request.form.get("demands", ""),
        )
    elif doc_type == "appeal":
        generated = generate_appeal(
            appeal_court_name=request.form.get("appeal_court_name", ""),
            first_court_name=request.form.get("first_court_name", ""),
            case_number=request.form.get("case_number", ""),
            appellant=request.form.get("appellant", ""),
            appellant_address=request.form.get("appellant_address", ""),
            opponent=request.form.get("opponent", ""),
            decision_date=request.form.get("decision_date", ""),
            grounds=request.form.get("grounds", ""),
            demands=request.form.get("demands", ""),
        )
    elif doc_type == "motion":
        generated = generate_motion(
            court_name=request.form.get("court_name", ""),
            case_number=request.form.get("case_number", ""),
            applicant=request.form.get("applicant", ""),
            motion_type=request.form.get("motion_type", ""),
            justification=request.form.get("justification", ""),
            request=request.form.get("request", ""),
        )
    elif doc_type == "court_order":
        amount = 0.0
        try:
            amount = float(request.form.get("amount", 0))
        except (ValueError, TypeError):
            pass
        generated = generate_court_order_application(
            court_name=request.form.get("court_name", ""),
            applicant=request.form.get("applicant", ""),
            applicant_address=request.form.get("applicant_address", ""),
            debtor=request.form.get("debtor", ""),
            debtor_address=request.form.get("debtor_address", ""),
            amount=amount,
            basis=request.form.get("basis", ""),
        )

    return render_template(
        "documents.html",
        doc_types=DOCUMENT_TYPES,
        doc_type=doc_type,
        generated_doc=generated,
    )


# ============================================================
# Batch processing
# ============================================================

@app.route("/batch", methods=["GET", "POST"])
@login_required
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


# ============================================================
# Official sources
# ============================================================

@app.route("/official-sources")
@login_required
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


# ============================================================
# Normalize
# ============================================================

@app.route("/normalize", methods=["GET", "POST"])
@login_required
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


# ============================================================
# API: stats for charts
# ============================================================

@app.route("/api/stats")
@login_required
def api_stats():
    uid = current_user_id()
    stats = case_mgr.stats(user_id=uid)
    return json.dumps(stats, ensure_ascii=False)


if __name__ == "__main__":
    app.run(debug=True)
