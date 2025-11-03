"""
Flask застосунок для нормалізації адрес та пошуку районних судів
"""
from flask import Flask, request, render_template, send_file, redirect, url_for, jsonify
import csv
import io
import os
from typing import List, Dict
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

# Імпорт власних модулів
from address_normalizer import AddressNormalizer
from court_finder import CourtFinder

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB максимум

# Ініціалізація модулів
normalizer = AddressNormalizer()
court_finder = CourtFinder()


def process_address_row(row: Dict[str, str], normalize: bool = True) -> Dict[str, any]:
    """
    Обробка одного рядка адреси

    Args:
        row: Словник з даними адреси
        normalize: Чи нормалізувати адресу

    Returns:
        Оброблений словник з результатами
    """
    result = {
        'original_address': '',
        'normalized_address': '',
        'oblast': '',
        'district': '',
        'city': '',
        'street': '',
        'house': '',
        'apartment': '',
        'postal_code': '',
        'court_name': '',
        'court_address': '',
        'court_phone': '',
        'match_score': 0,
        'status': 'success',
        'error': ''
    }

    try:
        # Якщо є повна адреса в одному полі
        if 'address' in row and row['address']:
            full_address = row['address']
            result['original_address'] = full_address

            if normalize:
                # Розбір та нормалізація
                normalized_dict, formatted = normalizer.normalize_full_address(full_address)
                result.update(normalized_dict)
                result['normalized_address'] = formatted
            else:
                # Тільки розбір без нормалізації
                parsed = normalizer.parse_full_address(full_address)
                result.update(parsed)
                result['normalized_address'] = full_address

        # Або окремі поля
        else:
            address_dict = {
                'oblast': row.get('oblast', ''),
                'district': row.get('district', ''),
                'city': row.get('city', '') or row.get('settlement', ''),
                'street': row.get('street', ''),
                'house': row.get('house', ''),
                'apartment': row.get('apartment', ''),
                'postal_code': row.get('postal_code', '')
            }

            result['original_address'] = ', '.join(
                v for v in address_dict.values() if v
            )

            if normalize:
                normalized_dict = normalizer.normalize_address(address_dict)
                result.update(normalized_dict)
                result['normalized_address'] = normalizer.format_normalized_address(
                    normalized_dict
                )
            else:
                result.update(address_dict)
                result['normalized_address'] = result['original_address']

        # Пошук суду
        search_dict = {
            'oblast': result['oblast'],
            'district': result['district'],
            'city': result['city']
        }

        court_result = court_finder.find_court_by_address(search_dict)

        if court_result:
            result['court_name'] = court_result['court_name']
            result['court_address'] = court_result['court_address']
            result['court_phone'] = court_result.get('court_phone', '')
            result['match_score'] = court_result.get('match_score', 0)
        else:
            result['status'] = 'warning'
            result['error'] = 'Суд не знайдено для даної адреси'

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)

    return result


@app.route("/", methods=["GET"])
def index():
    """Головна сторінка"""
    stats = court_finder.get_statistics()
    return render_template("index.html", stats=stats)


@app.route("/single", methods=["GET", "POST"])
def single():
    """Обробка одиничної адреси"""
    if request.method == "POST":
        # Отримання даних форми
        address_data = {
            'oblast': request.form.get('oblast', ''),
            'district': request.form.get('district', ''),
            'city': request.form.get('city', ''),
            'street': request.form.get('street', ''),
            'house': request.form.get('house', ''),
            'apartment': request.form.get('apartment', ''),
            'postal_code': request.form.get('postal_code', '')
        }

        # Або повна адреса
        if request.form.get('full_address'):
            address_data = {'address': request.form.get('full_address')}

        normalize = request.form.get('normalize', 'on') == 'on'

        # Обробка
        result = process_address_row(address_data, normalize=normalize)

        return render_template("result.html", result=result)

    return render_template("single.html")


@app.route("/batch", methods=["GET", "POST"])
def batch():
    """Пакетна обробка з файлів"""
    if request.method == "POST":
        file = request.files.get("file")
        normalize = request.form.get('normalize', 'on') == 'on'

        if not file:
            return render_template(
                "batch.html",
                error="Будь ласка, завантажте файл"
            )

        # Перевірка розширення файлу
        filename = file.filename.lower()

        try:
            if filename.endswith('.csv'):
                # Обробка CSV
                stream = io.StringIO(file.stream.read().decode("utf-8"))
                reader = csv.DictReader(stream)
                rows = list(reader)

            elif filename.endswith(('.xlsx', '.xls')):
                # Обробка Excel
                df = pd.read_excel(file)
                rows = df.to_dict('records')

            else:
                return render_template(
                    "batch.html",
                    error="Непідтримуваний формат файлу. Використовуйте CSV або XLSX"
                )

            # Обробка рядків
            processed = []
            for idx, row in enumerate(rows, 1):
                result = process_address_row(row, normalize=normalize)
                result['row_number'] = idx
                processed.append(result)

            return render_template("batch_result.html", rows=processed)

        except Exception as e:
            return render_template(
                "batch.html",
                error=f"Помилка обробки файлу: {str(e)}"
            )

    return render_template("batch.html")


@app.route("/export/<format>", methods=["POST"])
def export(format):
    """Експорт результатів"""
    try:
        data = request.json
        rows = data.get('rows', [])

        if format == 'csv':
            return export_csv(rows)
        elif format == 'xlsx':
            return export_xlsx(rows)
        else:
            return jsonify({'error': 'Непідтримуваний формат'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def export_csv(rows: List[Dict]) -> any:
    """Експорт у CSV формат"""
    output = io.StringIO()

    if not rows:
        return jsonify({'error': 'Немає даних для експорту'}), 400

    fieldnames = [
        'row_number', 'original_address', 'normalized_address',
        'oblast', 'district', 'city', 'street', 'house', 'apartment',
        'postal_code', 'court_name', 'court_address', 'court_phone',
        'match_score', 'status', 'error'
    ]

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow({k: row.get(k, '') for k in fieldnames})

    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"address_results_{timestamp}.csv"

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


def export_xlsx(rows: List[Dict]) -> any:
    """Експорт у Excel формат"""
    if not rows:
        return jsonify({'error': 'Немає даних для експорту'}), 400

    wb = Workbook()
    ws = wb.active
    ws.title = "Результати обробки"

    # Заголовки
    headers = [
        '№', 'Оригінальна адреса', 'Нормалізована адреса',
        'Область', 'Район', 'Місто', 'Вулиця', 'Будинок', 'Квартира',
        'Індекс', 'Назва суду', 'Адреса суду', 'Телефон суду',
        'Точність (%)', 'Статус', 'Помилка'
    ]

    # Стилі для заголовків
    header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)

    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center', vertical='center')

    # Дані
    for row_num, row in enumerate(rows, 2):
        ws.cell(row=row_num, column=1, value=row.get('row_number', row_num - 1))
        ws.cell(row=row_num, column=2, value=row.get('original_address', ''))
        ws.cell(row=row_num, column=3, value=row.get('normalized_address', ''))
        ws.cell(row=row_num, column=4, value=row.get('oblast', ''))
        ws.cell(row=row_num, column=5, value=row.get('district', ''))
        ws.cell(row=row_num, column=6, value=row.get('city', ''))
        ws.cell(row=row_num, column=7, value=row.get('street', ''))
        ws.cell(row=row_num, column=8, value=row.get('house', ''))
        ws.cell(row=row_num, column=9, value=row.get('apartment', ''))
        ws.cell(row=row_num, column=10, value=row.get('postal_code', ''))
        ws.cell(row=row_num, column=11, value=row.get('court_name', ''))
        ws.cell(row=row_num, column=12, value=row.get('court_address', ''))
        ws.cell(row=row_num, column=13, value=row.get('court_phone', ''))
        ws.cell(row=row_num, column=14, value=row.get('match_score', 0))
        ws.cell(row=row_num, column=15, value=row.get('status', ''))
        ws.cell(row=row_num, column=16, value=row.get('error', ''))

    # Автоматична ширина колонок
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width

    # Збереження у буфер
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"address_results_{timestamp}.xlsx"

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route("/api/normalize", methods=["POST"])
def api_normalize():
    """API endpoint для нормалізації адреси"""
    try:
        data = request.json
        address = data.get('address', '')

        if not address:
            return jsonify({'error': 'Адреса не надана'}), 400

        normalized_dict, formatted = normalizer.normalize_full_address(address)

        return jsonify({
            'success': True,
            'original': address,
            'normalized': formatted,
            'components': normalized_dict
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/find_court", methods=["POST"])
def api_find_court():
    """API endpoint для пошуку суду"""
    try:
        data = request.json
        address_dict = {
            'oblast': data.get('oblast', ''),
            'district': data.get('district', ''),
            'city': data.get('city', '')
        }

        court_result = court_finder.find_court_by_address(address_dict)

        if court_result:
            return jsonify({
                'success': True,
                'court': court_result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Суд не знайдено'
            }), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/courts", methods=["GET"])
def courts_list():
    """Список всіх судів"""
    courts = court_finder.get_all_courts()
    stats = court_finder.get_statistics()

    return render_template("courts_list.html", courts=courts, stats=stats)


@app.route("/help", methods=["GET"])
def help_page():
    """Сторінка допомоги"""
    return render_template("help.html")


@app.errorhandler(413)
def too_large(e):
    """Обробка помилки завеликого файлу"""
    return "Файл занадто великий. Максимальний розмір - 16MB", 413


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
