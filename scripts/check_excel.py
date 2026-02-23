"""
Скрипт для перегляду структури Excel файлу судів
"""
import pandas as pd
import sys

# Шлях до вашого файлу
EXCEL_FILE = r"C:\Users\Nick\OneDrive\Рабочий стол\CoutParser\portfolio.xlsx"

print("Читання файлу...")
df = pd.read_excel(EXCEL_FILE, header=0)

print(f"\nВсього рядків: {len(df)}")
print(f"Всього колонок: {len(df.columns)}")

print("\n=== ВСІ КОЛОНКИ ===")
for i, col in enumerate(df.columns):
    col_letter = ""
    n = i + 1
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        col_letter = chr(65 + remainder) + col_letter
    print(f"  {col_letter} ({i+1}): {col}")

print("\n=== КОЛОНКА BM (65) ===")
bm_index = 64  # BM = 65-та колонка, індекс 64
if len(df.columns) > bm_index:
    bm_col = df.columns[bm_index]
    print(f"Назва колонки BM: '{bm_col}'")
    print(f"\nПерші 5 значень:")
    for val in df.iloc[:5, bm_index]:
        print(f"  {val}")

print("\n=== ПЕРШИЙ РЯДОК ДАНИХ ===")
print(df.iloc[0].to_string())
