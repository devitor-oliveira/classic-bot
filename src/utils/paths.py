# -*- coding: utf-8 -*-
"""
Resolve a pasta 'Documentos' do usuário e cria:
Documentos/classicbot/{logs, report_html, report_json, scans}
"""
from __future__ import annotations
import os
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Dict

def _windows_documents_dir() -> Path | None:
    """Usa SHGetKnownFolderPath(FOLDERID_Documents) para obter 'Documentos'."""
    try:
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8),
            ]
        FOLDERID_Documents = GUID(
            0xFDD39AD0, 0x238F, 0x46AF,
            (ctypes.c_ubyte * 8)(0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7)
        )
        SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
        SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_wchar_p)]
        SHGetKnownFolderPath.restype = wintypes.HRESULT

        path_ptr = ctypes.c_wchar_p()
        hr = SHGetKnownFolderPath(ctypes.byref(FOLDERID_Documents), 0, None, ctypes.byref(path_ptr))
        if hr != 0:
            return None
        path = Path(path_ptr.value)
        ctypes.windll.ole32.CoTaskMemFree(path_ptr)
        return path
    except Exception:
        return None

def _xdg_documents_dir() -> Path | None:
    """Linux: segue XDG user-dirs (~/.config/user-dirs.dirs → XDG_DOCUMENTS_DIR)."""
    try:
        cfg = Path.home() / ".config" / "user-dirs.dirs"
        if not cfg.exists():
            return None
        text = cfg.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("XDG_DOCUMENTS_DIR="):
                val = line.split("=", 1)[1].strip().strip('"')
                val = val.replace("$HOME", str(Path.home()))
                return Path(val)
        return None
    except Exception:
        return None

def get_documents_dir() -> Path:
    if sys.platform.startswith("win"):
        p = _windows_documents_dir()
        return p if p else Path.home() / "Documents"
    else:
        p = _xdg_documents_dir()
        return p if p else Path.home() / "Documents"

def classicbot_dirs() -> Dict[str, Path]:
    base = get_documents_dir() / "classicbot"
    logs = base / "logs"
    html = base / "report_html"
    jso = base / "report_json"
    scans = base / "scans"
    for d in (base, logs, html, jso, scans):
        d.mkdir(parents=True, exist_ok=True)
    return {"base": base, "logs": logs, "report_html": html, "report_json": jso, "scans": scans}
