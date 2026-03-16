"""AES-256 encryption for export files and backups."""

import os
import struct
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


def encrypt_file(input_path: Path, output_path: Path, key: bytes) -> None:
    """Encrypt a file using AES-256-CBC.

    Args:
        input_path: Source file to encrypt.
        output_path: Destination for encrypted file.
        key: 32-byte AES-256 key.
    """
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = PKCS7(128).padder()

    with open(input_path, "rb") as fin, open(output_path, "wb") as fout:
        # Write IV at the beginning
        fout.write(iv)
        # Write original file size for accurate decryption
        file_size = input_path.stat().st_size
        fout.write(struct.pack("<Q", file_size))

        while True:
            chunk = fin.read(64 * 1024)
            if not chunk:
                break
            padded = padder.update(chunk)
            fout.write(encryptor.update(padded))

        padded = padder.finalize()
        fout.write(encryptor.update(padded))
        fout.write(encryptor.finalize())


def decrypt_file(input_path: Path, output_path: Path, key: bytes) -> None:
    """Decrypt an AES-256-CBC encrypted file.

    Args:
        input_path: Encrypted file.
        output_path: Destination for decrypted file.
        key: 32-byte AES-256 key.
    """
    with open(input_path, "rb") as fin:
        iv = fin.read(16)
        original_size = struct.unpack("<Q", fin.read(8))[0]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        unpadder = PKCS7(128).unpadder()

        with open(output_path, "wb") as fout:
            while True:
                chunk = fin.read(64 * 1024)
                if not chunk:
                    break
                decrypted = unpadder.update(decryptor.update(chunk))
                fout.write(decrypted)

            decrypted = unpadder.update(decryptor.finalize())
            fout.write(decrypted)
            fout.write(unpadder.finalize())

    # Truncate to original size (remove padding bytes)
    with open(output_path, "r+b") as f:
        f.truncate(original_size)
