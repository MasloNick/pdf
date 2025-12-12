"""
Скрипт для імпорту судів з Excel файлу в JSON базу даних
"""
import pandas as pd
import json
import sys
import os

def import_courts_from_excel(excel_file_path, output_json_path):
    """
    Імпорт судів з Excel файлу

    Args:
        excel_file_path: Шлях до Excel файлу
        output_json_path: Шлях до вихідного JSON файлу
    """
    print(f"Читання Excel файлу: {excel_file_path}")

    # Читання Excel файлу
    df = pd.read_excel(excel_file_path)

    print(f"Знайдено {len(df)} судів")

    # Конвертація в структуру JSON
    courts = []

    for idx, row in df.iterrows():
        # Отримання даних з рядка
        court_id = str(row.get('ID_API', '')).strip()
        name = str(row.get('Назва суду API', '')).strip()
        edrpou = str(row.get('ЄДРПОУ', '')).strip()
        address = str(row.get('Адрес', '')).strip()
        email = str(row.get('Email&', '')).strip()
        iban = str(row.get('IBAN', '')).strip()
        bank = str(row.get('Банк', '')).strip()
        mfo = str(row.get('МФО', '')).strip()
        recipient = str(row.get('Отримувач', '')).strip()
        payment_code = str(row.get('Код платежу', '')).strip()
        district = str(row.get('Адміністративний район/Місто', '')).strip()
        oblast = str(row.get('Адміністративний район/Область', '')).strip()
        court_type = str(row.get('Тип суду', '')).strip()
        jurisdiction_text = str(row.get('Підсудність', '')).strip()

        # Визначення міста з адреси
        city = ""
        if address:
            # Спроба витягти місто з адреси
            parts = address.split(',')
            for part in parts:
                part = part.strip()
                if part.startswith('м.') or part.startswith('смт.') or part.startswith('с.'):
                    city = part
                    break

        # Визначення статусу (діючий чи переміщений)
        status = "діючий"
        relocated_address = ""

        # Парсинг юрисдикції
        jurisdiction_districts = []
        jurisdiction_settlements = []

        if jurisdiction_text and jurisdiction_text != 'nan':
            # Розбір тексту підсудності
            jurisdiction_districts.append(district)

        # Створення запису суду
        court = {
            "id": court_id,
            "name": name,
            "code": f"COURT_{court_id}",
            "type": court_type.lower() if court_type != 'nan' else "районний",
            "oblast": oblast,
            "city": city if city else district,
            "district": district,
            "address": address,
            "phone": "",  # Немає в даних
            "email": email if email != 'nan' else "",
            "edrpou": edrpou,
            "status": status,
            "relocated_address": relocated_address,
            "payment_details": {
                "recipient": recipient,
                "bank": bank,
                "mfo": mfo,
                "iban": iban,
                "edrpou": edrpou,
                "payment_code": payment_code
            },
            "jurisdiction": {
                "oblast": [oblast],
                "districts": jurisdiction_districts,
                "settlements": jurisdiction_settlements
            },
            "jurisdiction_description": jurisdiction_text if jurisdiction_text != 'nan' else ""
        }

        courts.append(court)

        # Прогрес
        if (idx + 1) % 50 == 0:
            print(f"Оброблено {idx + 1} судів...")

    # Створення фінальної структури
    courts_db = {
        "version": "1.0",
        "updated": "2025-12-12",
        "total_courts": len(courts),
        "courts": courts
    }

    # Збереження в JSON
    print(f"\nЗбереження в {output_json_path}")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(courts_db, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Успішно імпортовано {len(courts)} судів!")
    print(f"📊 Статистика:")

    # Статистика по областях
    oblasts = {}
    for court in courts:
        oblast = court['oblast']
        oblasts[oblast] = oblasts.get(oblast, 0) + 1

    print(f"\nСудів по областях:")
    for oblast, count in sorted(oblasts.items()):
        print(f"  {oblast}: {count}")

    return courts_db


if __name__ == "__main__":
    # Шляхи до файлів
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)

    # Excel файл має бути в папці data/
    excel_file = os.path.join(base_dir, 'data', 'courts_full.xlsx')

    # Вихідний JSON файл
    output_file = os.path.join(base_dir, 'data', 'courts.json')

    # Перевірка наявності Excel файлу
    if not os.path.exists(excel_file):
        print(f"❌ Помилка: Файл {excel_file} не знайдено!")
        print(f"\n📋 Інструкція:")
        print(f"1. Збережіть ваш Excel файл як: {excel_file}")
        print(f"2. Запустіть цей скрипт знову: python scripts/import_courts.py")
        sys.exit(1)

    # Імпорт даних
    try:
        import_courts_from_excel(excel_file, output_file)
        print(f"\n🎉 База даних успішно створена!")
        print(f"📁 Файл: {output_file}")
    except Exception as e:
        print(f"\n❌ Помилка при імпорті: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
