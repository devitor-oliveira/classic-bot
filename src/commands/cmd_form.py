# -*- coding: utf-8 -*-
"""
Comando: form
Fluxo completo alinhado ao /formulario/:
  - Abre home, clica no CTA, espera /formulario
  - Preenche Passo 1
  - Avança e espera resultados do Passo 2
  - (Opcional) ajusta slider
  - Avança para Passo 3
  - Marca aceite final e verifica se o botão de finalizar habilitou
  - (Opcional) FINALIZAR e PAGAR: normal ou forçado
Relatórios (HTML/JSON) em Documentos/classicbot/.
"""

from __future__ import annotations
import time
import logging
from pathlib import Path
import click

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from utils.paths import classicbot_dirs
from utils.driver_factory import create_chrome_driver
from reporters.html_reporter import HTMLReporter
from pages.form_page import FormPage

log = logging.getLogger("cmd_form")

DEFAULT_URL = "https://masterclassic.com.br"

@click.command(name="form", help="Executa o fluxo do formulário e gera relatório HTML.")
@click.option("--url", default=DEFAULT_URL, show_default=True, help="URL do site (home).")
@click.option("--nome", default="Teste QA", show_default=True)
@click.option("--email", default="qa@example.com", show_default=True)
@click.option("--nascimento", default="01/01/1990", show_default=True, help="Data de nascimento (DD/MM/AAAA).")
@click.option("--telefone", default="11999999999", show_default=True)
@click.option(
    "--renda",
    default="5000-7000",
    show_default=True,
    help="Valor do option em <select name='rendaMensal'> (ex.: 15000+, 10000-15000, 7000-10000, 5000-7000, ...)."
)
@click.option("--slider", default=None, type=int, help="Opcional: define valor do slider (cobertura principal).")
@click.option("--headed", is_flag=True, help="Executa com interface gráfica (sem headless).")
@click.option("--chrome-binary", default=None, help="Caminho para o Chrome (Windows) ou binário do navegador.")
@click.option("--finalizar", is_flag=True, help="(Perigoso) Clica em 'Pagar e Contratar' para testar backend.")
@click.option("--forcar-finalizar", is_flag=True, help="Força o clique (remove 'disabled' via JS) se o botão não habilitar.")
def cmd_form(url, nome, email, nascimento, telefone, renda, slider, headed, chrome_binary, finalizar, forcar_finalizar):
    dirs = classicbot_dirs()
    html_dir = dirs["report_html"]
    json_dir = dirs["report_json"]
    shots_dir = html_dir / "screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    reporter = HTMLReporter(out_dir=html_dir, json_out_dir=json_dir)
    driver = None

    try:
        # ---- HOME → CTA → /formulario/ ----
        log.info("Iniciando | headed=%s | url=%s", headed, url)
        reporter.add_step("Abrir navegador", "info", f"Headless: {not headed}")
        driver = create_chrome_driver(headless=not headed, chrome_binary=chrome_binary)

        driver.set_page_load_timeout(60)
        driver.get(url)
        reporter.add_step("Acessar site", "pass", f"URL: {url}")

        # clique no CTA “Simule Agora” da home
        from selenium.webdriver.common.by import By
        try:
            cta = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href$='/formulario/'], a[href*='/formulario']"))
            )
        except Exception:
            try:
                cta = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.LINK_TEXT, "Simule Agora")))
            except Exception:
                cta = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Simule")))
        reporter.add_step("Localizar CTA", "pass")

        prev = set(driver.window_handles)
        cta.click()

        # espera /formulario (mesma aba) ou troca pra nova aba e valida a URL
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.url_contains("/formulario"))  # recomendado para fragmento de URL
            reporter.add_step("Abrir /formulario", "pass", "URL contém /formulario")
        except Exception:
            new_handles = [h for h in driver.window_handles if h not in prev]
            if new_handles:
                driver.switch_to.window(new_handles[-1])
                wait.until(EC.url_contains("/formulario"))
                reporter.add_step("Trocar para nova aba", "pass", "Formulário ativo em nova aba")
            else:
                raise

        # ---- FORMULÁRIO: passos ----
        page = FormPage(driver)
        page.wait_form_ready()
        reporter.add_step("Formulário pronto (Passo 1)", "pass")

        # Passo 1
        page.fill_step1(nome=nome, email=email, nascimento=nascimento, telefone=telefone, renda_value=renda)
        reporter.add_step("Preencher Passo 1", "pass", f"nome={nome}, email={email}, nasc={nascimento}, tel={telefone}, renda={renda}")

        page.advance_from_step1()
        reporter.add_step("Avançar para Passo 2", "pass")

        # Passo 2
        if slider is not None:
            page.set_slider_if_needed(slider)
            reporter.add_step("Ajustar slider", "info", f"valor={slider}")
        page.next_from_step2()
        reporter.add_step("Avançar para Passo 3", "pass")

        # Passo 3
        page.accept_declarations()
        ready = page.is_ready_to_finalize()
        if ready:
            reporter.add_step("Aceite final", "pass", "Botão 'Pagar e Contratar' habilitado.")
        else:
            reporter.add_step("Aceite final", "info", "Botão não habilitou automaticamente.")

        # ---------- NOVO: execução opcional da finalização ----------
        if finalizar:
            if not click.confirm("⚠️  Isso pode acionar o backend real. Deseja prosseguir?", default=False):
                reporter.add_step("Finalização cancelada", "info", "Usuário optou por NÃO finalizar.")
            else:
                current_url = driver.current_url
                try:
                    page.finalize(force=forcar_finalizar)
                    reporter.add_step(
                        "Finalizar e pagar",
                        "pass" if not forcar_finalizar else "info",
                        "Clique enviado" + (" (forçado)" if forcar_finalizar else "")
                    )
                    try:
                        WebDriverWait(driver, 20).until(EC.url_changes(current_url))
                        reporter.add_step("Redirecionamento pós-finalização", "pass", f"Nova URL: {driver.current_url}")
                    except Exception:
                        reporter.add_step("Redirecionamento pós-finalização", "info", "Sem mudança de URL detectada.")
                except Exception as e:
                    reporter.add_step("Finalizar e pagar", "fail", f"Falha ao clicar: {e}")
        else:
            reporter.add_step("Finalização não executada", "info", "Use --finalizar para testar backend.")

        # Screenshot de sucesso
        shot_ok = shots_dir / f"success_{int(time.time()*1000)}.png"
        driver.save_screenshot(str(shot_ok))
        reporter.add_step("Captura de tela", "info", "Screenshot salvo",
                          screenshot=str(shot_ok.relative_to(html_dir)))

        reporter.save(open_in_browser=True)
        log.info("Fluxo do formulário finalizado com sucesso.")
        return 0

    except Exception as e:
        log.exception("Falha no fluxo do formulário: %s", e)
        try:
            if driver:
                shot_err = shots_dir / f"error_{int(time.time()*1000)}.png"
                driver.save_screenshot(str(shot_err))
                reporter.add_step("Captura de tela (erro)", "info", "Screenshot salvo",
                                  screenshot=str(shot_err.relative_to(html_dir)))
        except Exception:
            pass

        reporter.add_step("Erro durante o teste", "fail", str(e))
        reporter.save(open_in_browser=True)
        return 1

    finally:
        if driver:
            driver.quit()
