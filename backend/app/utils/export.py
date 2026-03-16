"""Export utilities: Excel and PDF generation with optional AES-256 encryption."""

import io
import os
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from openpyxl import Workbook


def export_to_excel(rows: list[dict], sheet_name: str = "Data") -> bytes:
    """Generate an Excel file from a list of dictionaries."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    if not rows:
        return _workbook_to_bytes(wb)

    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])

    return _workbook_to_bytes(wb)


def _workbook_to_bytes(wb: Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def encrypt_file_aes256(data: bytes, password: str) -> bytes:
    """Encrypt data with AES-256-GCM using a password-derived key."""
    # Derive a 256-bit key from password (simplified — use PBKDF2 in production)
    from hashlib import sha256

    key = sha256(password.encode()).digest()
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt_file_aes256(encrypted: bytes, password: str) -> bytes:
    """Decrypt AES-256-GCM encrypted data."""
    from hashlib import sha256

    key = sha256(password.encode()).digest()
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
