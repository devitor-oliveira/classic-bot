# -*- coding: utf-8 -*-
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

try:
    from webdriver_manager.chrome import ChromeDriverManager
except Exception:
    ChromeDriverManager = None  # type: ignore

log = logging.getLogger("driver_factory")

def _find_chrome_on_windows() -> Optional[str]:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%USERPROFILE%\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

def create_chrome_driver(headless: bool = True, chrome_binary: Optional[str] = None) -> webdriver.Chrome:
    """
    Compatibilidade máxima:
    - Usa Selenium Manager por padrão (Service() vazio).
    - Fallback para webdriver-manager se necessário.
    - Mantém detecção do Chrome no Windows.
    - Usa '--headless=new' quando headless=True.
    - Habilita 'goog:loggingPrefs' para capturar logs do navegador (LogType.BROWSER).
    """
    opts = ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1280,800")
    opts.add_argument("--lang=pt-BR")

    # Habilita logs do navegador (console) — Selenium 4: set_capability('goog:loggingPrefs', {...})
    # Docs: Logging (Selenium) + Chrome Devs (capabilities)
    opts.set_capability("goog:loggingPrefs", {"browser": "ALL"})  # :contentReference[oaicite:5]{index=5}

    if os.name == "nt" and not chrome_binary:
        chrome_binary = _find_chrome_on_windows()
    if chrome_binary:
        opts.binary_location = chrome_binary

    # 1) Selenium Manager
    try:
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=opts)
        log.debug("Driver criado via Selenium Manager.")
        return driver
    except Exception as e:
        log.warning("Selenium Manager falhou: %s", e)

    # 2) webdriver-manager
    if ChromeDriverManager:
        try:
            path = ChromeDriverManager().install()
            service = ChromeService(executable_path=path)
            driver = webdriver.Chrome(service=service, options=opts)
            log.debug("Driver criado via webdriver-manager.")
            return driver
        except Exception as e:
            log.error("webdriver-manager falhou: %s", e)

    # 3) Último recurso
    driver = webdriver.Chrome(options=opts)
    log.debug("Driver criado via webdriver.Chrome() sem Service explícito.")
    return driver

def get_browser_console_logs(driver: webdriver.Chrome) -> List[Dict[str, Any]]:
    """
    Coleta logs 'browser' do Chrome. Retorna lista (pode estar vazia).
    """
    entries: List[Dict[str, Any]] = []
    try:
        for e in driver.get_log("browser"):
            entries.append({
                "level": e.get("level"),
                "message": e.get("message"),
                "timestamp": e.get("timestamp"),
            })
    except Exception as err:
        log.debug("Falha ao coletar console logs: %s", err)
    return entries
