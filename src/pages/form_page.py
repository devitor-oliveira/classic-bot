# -*- coding: utf-8 -*-
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from .base_page import BasePage

class FormPage(BasePage):
    """
    Fluxo do formulário em /formulario/.
    IDs/classes conforme a página enviada:
      - form#vidaSeguroForm
      - step-1: campos e botão #btnNextStep1
      - step-2: slider #coberturaVidaSlider, loading #coverageLoading, resultados #coverageResults
      - barra de navegação: #mainNavigationButtons com #btnNext / #btnPrev
      - step-3: checkbox #aceiteFinalTodasDeclaracoes e botão #btnFinalizarProposta
    """

    # Form e passos
    FORM = (By.ID, "vidaSeguroForm")
    STEP1 = (By.ID, "step-1")
    STEP2 = (By.ID, "step-2")
    STEP3 = (By.ID, "step-3")

    # Step 1: campos
    FIELD_NOME = (By.ID, "contratanteNome")
    FIELD_EMAIL = (By.ID, "contratanteEmail")
    FIELD_NASC = (By.ID, "dataNascimento")
    FIELD_TEL = (By.ID, "contratanteTelefone")
    FIELD_RENDA = (By.ID, "rendaMensal")

    # Step 1: avançar
    BTN_NEXT_STEP1 = (By.ID, "btnNextStep1")

    # Controles globais de navegação
    MAIN_NAV = (By.ID, "mainNavigationButtons")
    BTN_NEXT = (By.ID, "btnNext")
    BTN_PREV = (By.ID, "btnPrev")

    # Step 2
    LOADING_STEP2 = (By.ID, "coverageLoading")
    RESULTS_STEP2 = (By.ID, "coverageResults")
    SLIDER_VIDA = (By.ID, "coberturaVidaSlider")

    # Step 3 (finalização)
    CHECK_ACEITE = (By.ID, "aceiteFinalTodasDeclaracoes")
    BTN_FINALIZAR = (By.ID, "btnFinalizarProposta")

    def wait_form_ready(self):
        """Espera o form carregar e o Passo 1 ficar visível."""
        self.wait.until(EC.presence_of_element_located(self.FORM))
        self.wait.until(EC.visibility_of_element_located(self.STEP1))

    # ---------- STEP 1 ----------
    def fill_step1(self, nome: str, email: str, nascimento: str, telefone: str, renda_value: str | None):
        self.type(*self.FIELD_NOME, text=nome)
        self.type(*self.FIELD_EMAIL, text=email)
        self.type(*self.FIELD_NASC, text=nascimento)  # ex.: 01/01/1990
        self.type(*self.FIELD_TEL, text=telefone)

        if renda_value:
            renda_el = self.find(*self.FIELD_RENDA)
            Select(renda_el).select_by_value(renda_value)  # classe Select p/ <select>  :contentReference[oaicite:2]{index=2}

    def advance_from_step1(self):
        self.click(*self.BTN_NEXT_STEP1)
        # loader pode ou não aparecer — se aparecer, espere sumir; depois espere resultados/controles
        try:
            self.wait.until(EC.presence_of_element_located(self.LOADING_STEP2))
        except Exception:
            pass
        WebDriverWait(self.driver, self.wait._timeout).until(EC.invisibility_of_element_located(self.LOADING_STEP2))
        self.wait.until(EC.visibility_of_element_located(self.RESULTS_STEP2))
        self.wait.until(EC.visibility_of_element_located(self.MAIN_NAV))

    # ---------- STEP 2 ----------
    def set_slider_if_needed(self, value: int | None = None):
        """Ajusta o slider principal se o teste quiser validar ranges (opcional)."""
        if value is None:
            return
        el = self.find(*self.SLIDER_VIDA)
        # Ajuste via JS + eventos (input/change) para disparar listeners do app.
        self.driver.execute_script(
            """
            const s = arguments[0], v = arguments[1];
            s.value = v;
            s.dispatchEvent(new Event('input', {bubbles: true}));
            s.dispatchEvent(new Event('change', {bubbles: true}));
            """,
            el, int(value)
        )

    def next_from_step2(self):
        self.click(*self.BTN_NEXT)
        self.wait.until(EC.visibility_of_element_located(self.STEP3))

    # ---------- STEP 3 ----------
    def accept_declarations(self):
        self.click(*self.CHECK_ACEITE)
        self.wait.until(EC.element_to_be_clickable(self.BTN_FINALIZAR))

    def is_ready_to_finalize(self) -> bool:
        try:
            btn = self.find(*self.BTN_FINALIZAR)
            return btn.is_enabled()
        except Exception:
            return False

    def finalize(self, force: bool = False) -> bool:
        """
        Clica no botão 'Pagar e Contratar'.
        - Normal: espera ficar clicável e clica.
        - force=True: remove 'disabled' via JS e clica (força).
        """
        try:
            btn = self.wait.until(EC.element_to_be_clickable(self.BTN_FINALIZAR))
            btn.click()
            return True
        except Exception:
            if not force:
                raise

        # modo forçado: habilita e clica via JS
        btn = self.find(*self.BTN_FINALIZAR)
        self.driver.execute_script("arguments[0].removeAttribute('disabled');", btn)
        self.driver.execute_script("arguments[0].click();", btn)
        return True
