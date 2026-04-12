"""HTML report generator for portfolio analysis.

Produces a standalone HTML document with embedded CSS that can be
printed to PDF from any browser via Ctrl+P.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List


def _fmt(val: Any) -> str:
    if val is None:
        return "—"
    try:
        v = float(val)
        if v == int(v) and abs(v) < 1e15:
            return f"{int(v):,}".replace(",", " ")
        return f"{v:,.2f}".replace(",", " ")
    except (ValueError, TypeError):
        return str(val)


def _fmt_uah(val: Any) -> str:
    if val is None:
        return "—"
    return f"{_fmt(val)} грн"


def _fmt_pct(val: Any) -> str:
    if val is None:
        return "—"
    try:
        return f"{float(val) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(val)


def generate_html_report(
    summary: Dict[str, Any],
    scoring: Dict[str, Any],
    pricing: Dict[str, Any],
    records: List[Dict[str, Any]],
) -> str:
    """Generate a complete standalone HTML report."""

    date_str = time.strftime("%d.%m.%Y %H:%M")

    rec_color = {"BUY": "#27ae60", "CONSIDER": "#f39c12", "PASS": "#e74c3c"}
    rec_label = {"BUY": "КУПУВАТИ", "CONSIDER": "РОЗГЛЯНУТИ", "PASS": "ПРОПУСТИТИ"}
    rec = scoring.get("recommendation", "CONSIDER")

    # Top debtors table rows
    top_rows = ""
    for i, d in enumerate(scoring.get("top_debtors", [])[:10], 1):
        top_rows += f"""<tr>
            <td>{i}</td>
            <td>{d.get('name', '—')}</td>
            <td>{_fmt_uah(d.get('debt'))}</td>
            <td>{_fmt_uah(d.get('principal'))}</td>
            <td>{d.get('score', 0)}/100</td>
            <td>{d.get('grade', '—')}</td>
            <td>{_fmt_uah(d.get('recovery'))}</td>
        </tr>"""

    # Risk flags
    risk_items = "".join(f"<li>{f}</li>" for f in scoring.get("risk_flags", []))
    risk_section = f"<ul>{risk_items}</ul>" if risk_items else "<p>Ризиків не виявлено.</p>"

    # Reasons
    reason_items = "".join(f"<li>{r}</li>" for r in scoring.get("recommendation_reasons", []))

    # Grade distribution
    grade_html = ""
    for grade, count in scoring.get("grade_distribution", {}).items():
        colors = {"A": "#d4edda", "B": "#d1ecf1", "C": "#fff3cd", "D": "#fde8d0", "F": "#f8d7da"}
        bg = colors.get(grade, "#eee")
        grade_html += f'<span style="display:inline-block;padding:6px 14px;margin:2px;border-radius:4px;background:{bg};font-weight:bold;">{grade}: {count}</span>'

    # Region rows
    region_rows = ""
    for region, count in summary.get("by_region", {}).items():
        region_rows += f"<tr><td>{region}</td><td>{count}</td></tr>"

    # Debt ranges
    range_rows = ""
    for label, count in summary.get("debt_ranges", {}).items():
        range_rows += f"<tr><td>{label}</td><td>{count}</td></tr>"

    # Adjustments
    adj_items = "".join(f"<li>{a}</li>" for a in pricing.get("adjustments_applied", []))

    return f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<title>Аналіз NPL-портфеля — {date_str}</title>
<style>
@page {{ size: A4; margin: 15mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; font-size: 12px; color: #222; margin: 0; padding: 20px; }}
h1 {{ font-size: 20px; color: #1a252f; border-bottom: 2px solid #2c3e50; padding-bottom: 8px; }}
h2 {{ font-size: 15px; color: #2c3e50; margin-top: 24px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
table {{ border-collapse: collapse; width: 100%; margin: 8px 0; }}
th, td {{ padding: 5px 8px; border: 1px solid #ccc; text-align: left; font-size: 11px; }}
th {{ background: #f0f0f0; font-weight: 600; }}
.stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 10px 0; }}
.stat {{ border: 1px solid #ddd; border-radius: 6px; padding: 10px 16px; text-align: center; min-width: 140px; }}
.stat .num {{ font-size: 18px; font-weight: bold; color: #2c3e50; }}
.stat .lbl {{ font-size: 10px; color: #777; }}
.rec {{ display: inline-block; padding: 6px 18px; border-radius: 4px; color: #fff; font-weight: bold; font-size: 14px; }}
.bar {{ height: 10px; border-radius: 3px; display: inline-block; }}
ul {{ padding-left: 20px; }}
li {{ margin: 2px 0; }}
.warn {{ background: #fff3cd; border: 1px solid #ffc107; padding: 8px; border-radius: 4px; }}
.footer {{ margin-top: 30px; font-size: 10px; color: #999; border-top: 1px solid #ddd; padding-top: 8px; }}
@media print {{ body {{ padding: 0; }} }}
</style>
</head>
<body>

<h1>Аналіз NPL-портфеля</h1>
<p>Дата звіту: {date_str}</p>

<h2>1. Загальна інформація</h2>
<div class="stats">
    <div class="stat"><div class="num">{_fmt(summary.get('total_records'))}</div><div class="lbl">Записів</div></div>
    <div class="stat"><div class="num">{_fmt_uah(summary.get('total_debt'))}</div><div class="lbl">Загальний борг</div></div>
    <div class="stat"><div class="num">{_fmt_uah(summary.get('total_principal'))}</div><div class="lbl">Тіло кредиту</div></div>
    <div class="stat"><div class="num">{_fmt_uah(summary.get('avg_debt'))}</div><div class="lbl">Середня сума</div></div>
</div>
<table>
    <tr><th>Показник</th><th>Значення</th></tr>
    <tr><td>Фізичні особи</td><td>{_fmt(summary.get('physical_count'))}</td></tr>
    <tr><td>Юридичні особи</td><td>{_fmt(summary.get('legal_count'))}</td></tr>
    <tr><td>Медіана боргу</td><td>{_fmt_uah(summary.get('median_debt'))}</td></tr>
    <tr><td>Мінімальний борг</td><td>{_fmt_uah(summary.get('min_debt'))}</td></tr>
    <tr><td>Максимальний борг</td><td>{_fmt_uah(summary.get('max_debt'))}</td></tr>
</table>

<h2>2. Склад боргу</h2>
<table>
    <tr><th>Компонент</th><th>Сума</th><th>Частка</th></tr>
    <tr><td>Тіло кредиту</td><td>{_fmt_uah(summary.get('total_principal'))}</td><td><span class="bar" style="width:{int(summary.get('principal_ratio',0)*200)}px;background:#27ae60;"></span> {_fmt_pct(summary.get('principal_ratio'))}</td></tr>
    <tr><td>Відсотки</td><td>{_fmt_uah(summary.get('total_interest'))}</td><td><span class="bar" style="width:{int(summary.get('interest_ratio',0)*200)}px;background:#f39c12;"></span> {_fmt_pct(summary.get('interest_ratio'))}</td></tr>
    <tr><td>Пеня / штрафи</td><td>{_fmt_uah(summary.get('total_penalty'))}</td><td><span class="bar" style="width:{int(summary.get('penalty_ratio',0)*200)}px;background:#e74c3c;"></span> {_fmt_pct(summary.get('penalty_ratio'))}</td></tr>
</table>

<h2>3. Скоринг портфеля</h2>
<div class="stats">
    <div class="stat" style="border-color:{rec_color.get(rec, '#999')}"><div class="num">{scoring.get('overall_score', 0)}/100 ({scoring.get('overall_grade', '—')})</div><div class="lbl">Загальна оцінка</div></div>
    <div class="stat"><div class="num">{_fmt_uah(scoring.get('estimated_total_recovery'))}</div><div class="lbl">Очікуване стягнення ({_fmt_pct(scoring.get('avg_recovery_rate'))})</div></div>
    <div class="stat"><div class="num">{_fmt_uah(scoring.get('max_recommended_price'))}</div><div class="lbl">Макс. рекомендована ціна</div></div>
    <div class="stat" style="border-color:{rec_color.get(rec, '#999')}"><div class="rec" style="background:{rec_color.get(rec, '#999')}">{rec_label.get(rec, rec)}</div><div class="lbl">Рекомендація</div></div>
</div>
<p><strong>{scoring.get('quality_label', '')}</strong></p>
<p>Витрати на стягнення (оцінка): {_fmt_uah(scoring.get('collection_cost_estimate'))}</p>
{grade_html}
<h3 style="font-size:12px;">Обґрунтування</h3>
<ul>{reason_items}</ul>

<h2>4. Рекомендована ціна</h2>
<table>
    <tr><th></th><th>% від боргу</th><th>Сума</th></tr>
    <tr style="color:#27ae60"><td>Мінімум</td><td>{pricing.get('price_pct_low')}%</td><td>{_fmt_uah(pricing.get('recommended_price_low'))}</td></tr>
    <tr style="color:#f39c12;font-weight:bold"><td>Середня</td><td>{pricing.get('price_pct_mid')}%</td><td>{_fmt_uah(pricing.get('recommended_price_mid'))}</td></tr>
    <tr style="color:#e74c3c"><td>Максимум</td><td>{pricing.get('price_pct_high')}%</td><td>{_fmt_uah(pricing.get('recommended_price_high'))}</td></tr>
</table>
{f'<h3 style="font-size:12px;">Коригування</h3><ul>{adj_items}</ul>' if adj_items else ''}

<h2>5. Ризики</h2>
{risk_section}

<h2>6. ТОП-10 боржників</h2>
<table>
    <tr><th>#</th><th>Назва</th><th>Борг</th><th>Тіло</th><th>Оцінка</th><th>Грейд</th><th>Очік. стягнення</th></tr>
    {top_rows}
</table>

{f'''<h2>7. Регіональний розподіл</h2>
<table><tr><th>Регіон</th><th>Кількість</th></tr>{region_rows}</table>''' if region_rows else ''}

{f'''<h2>8. Розподіл за сумою боргу</h2>
<table><tr><th>Діапазон</th><th>Кількість</th></tr>{range_rows}</table>''' if range_rows else ''}

<div class="footer">
    NPL Portfolio Platform | Звіт згенеровано {date_str}
</div>

</body>
</html>"""
