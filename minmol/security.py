from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path


class DataBlob(ctypes.Structure):
    _fields_ = (("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte)))


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    blob = DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    return blob, buffer


def _require_windows():
    if os.name != "nt":
        raise OSError("Защищенное хранение API-ключа поддерживается только в Windows.")


def save_secret(secret: str, path: Path) -> None:
    _require_windows()
    source, source_buffer = _blob(secret.encode("utf-8"))
    encrypted = DataBlob()
    crypt32 = ctypes.windll.crypt32
    success = crypt32.CryptProtectData(
        ctypes.byref(source),
        None,
        None,
        None,
        None,
        0x01,
        ctypes.byref(encrypted),
    )
    del source_buffer
    if not success:
        raise ctypes.WinError()
    try:
        payload = ctypes.string_at(encrypted.pbData, encrypted.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(encrypted.pbData)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def load_secret(path: Path) -> str:
    if not path.exists():
        return ""
    _require_windows()
    source, source_buffer = _blob(path.read_bytes())
    decrypted = DataBlob()
    success = ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(source),
        None,
        None,
        None,
        None,
        0x01,
        ctypes.byref(decrypted),
    )
    del source_buffer
    if not success:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(decrypted.pbData, decrypted.cbData).decode("utf-8")
    finally:
        ctypes.windll.kernel32.LocalFree(decrypted.pbData)


def delete_secret(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
