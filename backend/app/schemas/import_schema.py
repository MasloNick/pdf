"""Import-related Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel


class ColumnMapping(BaseModel):
    source_column: str
    target_field: str


class ImportConfig(BaseModel):
    portfolio_id: Optional[int] = None
    portfolio_name: Optional[str] = None
    mode: str = "new"  # new / update / append
    column_mappings: list[ColumnMapping] = []
    template_name: Optional[str] = None
    save_template: bool = False


class ImportPreview(BaseModel):
    detected_columns: list[str]
    sample_rows: list[dict]
    detected_encoding: str
    total_rows: int
    suggested_mappings: list[ColumnMapping]


class ImportResult(BaseModel):
    task_id: str
    status: str  # pending / processing / completed / failed
    total_rows: int = 0
    processed: int = 0
    added: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[dict] = []
    error_file_url: Optional[str] = None
