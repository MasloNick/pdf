"""Portfolio import service — file parsing, validation, normalization."""

import os
import chardet
import pandas as pd
from typing import Optional
from app.schemas.import_schema import ImportPreview, ColumnMapping

# Known field mappings for auto-detection
FIELD_ALIASES = {
    "full_name": ["пib", "піб", "боржник", "повне ім'я", "full_name", "name", "fio"],
    "ipn": ["рнокпп", "інн", "іпн", "ipn", "inn", "tax_id"],
    "birth_date": ["дата народження", "birth_date", "дн", "birthday"],
    "phone_primary": ["телефон", "phone", "тел", "моб"],
    "email": ["email", "пошта", "e-mail"],
    "registration_address_raw": ["адреса", "адреса реєстрації", "address"],
    "credit_contract_number": ["номер договору", "договір", "contract", "кд"],
    "credit_contract_date": ["дата договору", "contract_date"],
    "original_creditor": ["кредитор", "банк", "creditor", "original_creditor"],
    "purchased_principal_uah": ["тіло", "основний борг", "principal", "тіло кредиту"],
    "purchased_interest_uah": ["відсотки", "проценти", "interest"],
    "purchased_penalty_uah": ["пеня", "штраф", "penalty"],
    "purchased_total_uah": ["загальний борг", "всього", "total", "сума боргу"],
    "passport_series": ["серія паспорта", "passport_series"],
    "passport_number": ["номер паспорта", "passport_number"],
    "product_type": ["тип продукту", "product", "тип кредиту"],
}


class ImportService:
    def detect_encoding(self, file_path: str) -> str:
        with open(file_path, "rb") as f:
            raw = f.read(10000)
        result = chardet.detect(raw)
        return result.get("encoding", "utf-8") or "utf-8"

    def generate_preview(self, file_path: str, ext: str) -> ImportPreview:
        if ext == ".csv":
            encoding = self.detect_encoding(file_path)
            df = pd.read_csv(file_path, encoding=encoding, nrows=20)
            total_rows = sum(1 for _ in open(file_path, encoding=encoding)) - 1
        else:
            df = pd.read_excel(file_path, nrows=20)
            df_full = pd.read_excel(file_path, usecols=[0])
            total_rows = len(df_full)

        columns = list(df.columns)
        sample_rows = df.head(20).fillna("").to_dict(orient="records")

        # Auto-suggest mappings
        suggested = self._suggest_mappings(columns)

        return ImportPreview(
            detected_columns=columns,
            sample_rows=sample_rows,
            detected_encoding=self.detect_encoding(file_path) if ext == ".csv" else "xlsx",
            total_rows=total_rows,
            suggested_mappings=suggested,
        )

    def _suggest_mappings(self, columns: list[str]) -> list[ColumnMapping]:
        mappings = []
        for col in columns:
            col_lower = col.lower().strip()
            for field, aliases in FIELD_ALIASES.items():
                if col_lower in aliases:
                    mappings.append(ColumnMapping(source_column=col, target_field=field))
                    break
        return mappings

    def validate_ipn(self, ipn: str) -> bool:
        """Validate Ukrainian IPN (РНОКПП) with checksum."""
        if not ipn or len(ipn) != 10 or not ipn.isdigit():
            return False
        weights = [-1, 5, 7, 9, 4, 6, 10, 5, 7]
        checksum = sum(int(ipn[i]) * weights[i] for i in range(9)) % 11 % 10
        return checksum == int(ipn[9])

    def parse_file(self, file_path: str, ext: str, encoding: Optional[str] = None) -> pd.DataFrame:
        """Parse full file into DataFrame."""
        if ext == ".csv":
            enc = encoding or self.detect_encoding(file_path)
            return pd.read_csv(file_path, encoding=enc)
        else:
            return pd.read_excel(file_path)
