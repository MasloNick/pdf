import csv
import sys

import pdfplumber


def process_pdf(pdf_path, csv_path, headers=None):
    out_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                out_rows.extend(table)

    if not out_rows:
        if headers:
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
        else:
            print(f"Warning: no rows found in {pdf_path}; no CSV created")
        return

    if headers is None:
        headers, *out_rows = out_rows

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(out_rows)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: process_pdf.py <input.pdf> <output.csv> [comma-separated headers]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    csv_path = sys.argv[2]
    headers = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    process_pdf(pdf_path, csv_path, headers)
