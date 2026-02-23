"""
Скрипт для обробки адрес з файлу portfolio.xlsx (колонка BM)
Аналізує структуру файлу, нормалізує адреси, знаходить суди

Запуск:
  python scripts\process_portfolio.py
"""
import pandas as pd
import json
import sys
import os
import re

# Додаємо шлях до модулів проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from address_normalizer import AddressNormalizer
from court_finder import CourtFinder


# === НАЛАШТУВАННЯ ===
PORTFOLIO_FILE = r"C:\Users\Nick\OneDrive\Рабочий стол\CoutParser\portfolio.xlsx"
ADDRESS_COLUMN = "BM"  # Колонка з адресами (салатова)
# ====================


def col_letter_to_index(letter):
    """Конвертація літери колонки Excel в індекс (A=0, B=1, ..., BM=64)"""
    result = 0
    for char in letter.upper():
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def analyze_file(df):
    """Крок 1: Аналіз структури файлу"""
    print("=" * 60)
    print("  КРОК 1: АНАЛІЗ СТРУКТУРИ ФАЙЛУ")
    print("=" * 60)
    print(f"\nВсього рядків: {len(df)}")
    print(f"Всього колонок: {len(df.columns)}")

    # Показати всі колонки
    print(f"\n--- Всі колонки ---")
    for i, col in enumerate(df.columns):
        n = i + 1
        col_letter = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            col_letter = chr(65 + remainder) + col_letter
        # Помітити колонку BM
        marker = " <<< АДРЕСИ" if col_letter == ADDRESS_COLUMN else ""
        print(f"  {col_letter:>3} ({i+1:>2}): {col}{marker}")

    return True


def extract_addresses(df):
    """Крок 2: Витягти адреси з колонки BM"""
    print("\n" + "=" * 60)
    print("  КРОК 2: ВИТЯГУВАННЯ АДРЕС")
    print("=" * 60)

    bm_index = col_letter_to_index(ADDRESS_COLUMN)

    if bm_index >= len(df.columns):
        print(f"❌ Колонка {ADDRESS_COLUMN} (індекс {bm_index}) не знайдена!")
        print(f"   Файл має тільки {len(df.columns)} колонок")
        return None

    col_name = df.columns[bm_index]
    print(f"Колонка {ADDRESS_COLUMN} = '{col_name}'")

    # Витягнути адреси
    addresses = df.iloc[:, bm_index].dropna().astype(str).tolist()
    addresses = [a.strip() for a in addresses if a.strip() and a.strip() != 'nan']

    print(f"Знайдено {len(addresses)} адрес")

    if addresses:
        print(f"\nПерші 5 адрес:")
        for i, addr in enumerate(addresses[:5], 1):
            print(f"  {i}. {addr}")

    return addresses, bm_index, col_name


def process_addresses(df, addresses, normalizer, court_finder):
    """Крок 3: Нормалізація адрес та пошук судів"""
    print("\n" + "=" * 60)
    print("  КРОК 3: НОРМАЛІЗАЦІЯ АДРЕС ТА ПОШУК СУДІВ")
    print("=" * 60)

    results = []
    success_count = 0
    warning_count = 0
    error_count = 0

    for idx, addr in enumerate(addresses, 1):
        try:
            # Нормалізація
            normalized_dict, formatted = normalizer.normalize_full_address(addr)

            # Пошук суду
            search_dict = {
                'oblast': normalized_dict.get('oblast', ''),
                'district': normalized_dict.get('district', ''),
                'city': normalized_dict.get('city', '')
            }
            court_result = court_finder.find_court_by_address(search_dict)

            result = {
                'row': idx,
                'original': addr,
                'normalized': formatted,
                'oblast': normalized_dict.get('oblast', ''),
                'district': normalized_dict.get('district', ''),
                'city': normalized_dict.get('city', ''),
                'street': normalized_dict.get('street', ''),
                'house': normalized_dict.get('house', ''),
                'postal_code': normalized_dict.get('postal_code', ''),
                'court_name': '',
                'court_address': '',
                'court_phone': '',
                'match_score': 0,
                'status': 'warning',
                'error': 'Суд не знайдено'
            }

            if court_result:
                result['court_name'] = court_result['court_name']
                result['court_address'] = court_result['court_address']
                result['court_phone'] = court_result.get('court_phone', '')
                result['match_score'] = court_result.get('match_score', 0)
                result['status'] = 'success'
                result['error'] = ''
                success_count += 1
            else:
                warning_count += 1

            results.append(result)

        except Exception as e:
            results.append({
                'row': idx,
                'original': addr,
                'normalized': '',
                'status': 'error',
                'error': str(e)
            })
            error_count += 1

        # Прогрес
        if idx % 50 == 0:
            print(f"  Оброблено {idx}/{len(addresses)}...")

    print(f"\n--- Результати ---")
    print(f"  Успішно (суд знайдено): {success_count}")
    print(f"  Суд не знайдено:        {warning_count}")
    print(f"  Помилки:                 {error_count}")

    return results


def save_results(df, results, bm_index, output_file):
    """Крок 4: Збереження результатів"""
    print("\n" + "=" * 60)
    print("  КРОК 4: ЗБЕРЕЖЕННЯ РЕЗУЛЬТАТІВ")
    print("=" * 60)

    # Створення нового DataFrame з результатами
    results_df = pd.DataFrame(results)

    # Зберігаємо як окремий Excel файл
    results_df.to_excel(output_file, index=False, sheet_name='Результати')

    print(f"✅ Результати збережено: {output_file}")
    print(f"   Всього рядків: {len(results)}")

    return output_file


def main():
    print("🏛️ Обробка адрес з portfolio.xlsx")
    print("=" * 60)

    # Перевірка файлу
    if not os.path.exists(PORTFOLIO_FILE):
        print(f"❌ Файл не знайдено: {PORTFOLIO_FILE}")
        print(f"\nПеревірте шлях до файлу!")
        sys.exit(1)

    # Ініціалізація
    normalizer = AddressNormalizer()
    court_finder = CourtFinder()

    print(f"📁 Файл: {PORTFOLIO_FILE}")
    print(f"📊 Колонка з адресами: {ADDRESS_COLUMN}")
    print(f"🏛️ Судів у базі: {len(court_finder.courts)}")

    # Читання файлу
    print(f"\nЧитання Excel файлу...")
    df = pd.read_excel(PORTFOLIO_FILE, header=0)

    # Крок 1: Аналіз
    analyze_file(df)

    # Крок 2: Витягування адрес
    result = extract_addresses(df)
    if result is None:
        sys.exit(1)

    addresses, bm_index, col_name = result

    if not addresses:
        print("❌ Адреси не знайдено!")
        sys.exit(1)

    # Крок 3: Обробка
    results = process_addresses(df, addresses, normalizer, court_finder)

    # Крок 4: Збереження
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    output_file = os.path.join(base_dir, 'data', 'portfolio_results.xlsx')

    # Також зберігаємо поруч з оригінальним файлом
    output_file_2 = os.path.join(
        os.path.dirname(PORTFOLIO_FILE),
        'portfolio_results.xlsx'
    )

    save_results(df, results, bm_index, output_file)
    save_results(df, results, bm_index, output_file_2)

    print(f"\n🎉 ГОТОВО!")
    print(f"📁 Результати збережено в:")
    print(f"   1. {output_file}")
    print(f"   2. {output_file_2}")
    print(f"\nВідкрийте файл portfolio_results.xlsx щоб побачити результати!")


if __name__ == "__main__":
    main()
