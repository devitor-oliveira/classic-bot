# -*- coding: utf-8 -*-
"""
Launcher da CLI do bot masterClassic
- MENU interativo
- Logs e relatórios em Documentos/classicbot/{logs, report_html, report_json, scans}
- Opções para abrir pastas no explorador
- Teste de formulário (com finalizar opcional)
- NOVO: Scan de página (gera inventário de elementos)
"""

from __future__ import annotations
import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import click

# --- paths para rodar local e em PyInstaller ---
APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)).resolve()
PROJECT_DIR = Path(__file__).parent.resolve()
SRC_DIR = PROJECT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# dirs de saída (Documentos/classicbot/…)
from utils.paths import classicbot_dirs

# comandos
from commands.cmd_form import cmd_form
from commands.cmd_scan import cmd_scan

# -------------------- logging --------------------
def setup_logging(verbose: bool = False) -> Path:
    dirs = classicbot_dirs()
    logs_dir = dirs["logs"]
    log_path = logs_dir / f"launcher_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler(log_path, encoding="utf-8")],
    )
    logging.getLogger("WDM").setLevel(logging.WARNING)
    return log_path

# -------------------- util: abrir pasta no SO --------------------
def open_in_file_manager(path: Path) -> bool:
    """Abre 'path' no explorador de arquivos do sistema."""
    try:
        path = path.resolve()
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return True
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
            return True
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
            return True
    except Exception:
        return False

# -------------------- CLI + MENU --------------------
@click.group(invoke_without_command=True, context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(message="classic-bot CLI")
@click.option("--verbose", is_flag=True, help="Ativa logs detalhados.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """Bot de testes do site masterclassic.com.br."""
    log_file = setup_logging(verbose=verbose)
    click.echo(f"📄 Log: {log_file}")

    if ctx.invoked_subcommand is None:
        _menu(ctx)

def _menu(ctx: click.Context):
    dirs = classicbot_dirs()
    html_dir = dirs["report_html"]
    json_dir = dirs["report_json"]
    logs_dir = dirs["logs"]
    scans_dir = dirs["scans"]

    while True:
        click.echo("\n=== masterClassic — Testes ===")
        click.echo("1) Testar FORMULÁRIO")
        click.echo("2) Abrir pasta de RELATÓRIOS (HTML)")
        click.echo("3) Abrir pasta de RELATÓRIOS (JSON)")
        click.echo("4) Abrir pasta de LOGS")
        click.echo("5) SCAN de página (inventário de elementos)")
        click.echo("6) Abrir pasta de SCANS")
        click.echo("0) Sair")

        choice = click.prompt("Escolha uma opção", type=int, default=1)
        if choice == 0:
            break

        elif choice == 1:
            url = click.prompt("URL do site", default="https://masterclassic.com.br")
            headed = click.confirm("Deseja ver o navegador durante o teste?", default=True)
            usar_padroes = click.confirm("Usar dados padrão do formulário?", default=True)
            finalizar = click.confirm("Deseja FINALIZAR e PAGAR (testar backend)?", default=False)
            forcar = False
            if finalizar:
                forcar = click.confirm("Forçar clique se o botão não habilitar?", default=False)

            params = dict(url=url, headed=headed, finalizar=finalizar, forcar_finalizar=forcar)
            if not usar_padroes:
                params.update(
                    nome=click.prompt("Nome", default="Teste QA"),
                    email=click.prompt("Email", default="qa@example.com"),
                    telefone=click.prompt("Telefone", default="11999999999"),
                    estado=click.prompt("Estado (UF)", default="SP"),
                    cidade=click.prompt("Cidade", default="São Paulo"),
                )
            try:
                ctx.invoke(cmd_form, **params)
            except SystemExit:
                pass

        elif choice == 2:
            click.echo(f"Abrindo: {html_dir}" if open_in_file_manager(html_dir) else f"Não foi possível abrir: {html_dir}")

        elif choice == 3:
            click.echo(f"Abrindo: {json_dir}" if open_in_file_manager(json_dir) else f"Não foi possível abrir: {json_dir}")

        elif choice == 4:
            click.echo(f"Abrindo: {logs_dir}" if open_in_file_manager(logs_dir) else f"Não foi possível abrir: {logs_dir}")

        elif choice == 5:
            url = click.prompt("URL da página a escanear", default="https://masterclassic.com.br")
            headed = click.confirm("Deseja ver o navegador durante o SCAN?", default=False)
            try:
                ctx.invoke(cmd_scan, url=url, headed=headed)
            except SystemExit:
                pass

        elif choice == 6:
            click.echo(f"Abrindo: {scans_dir}" if open_in_file_manager(scans_dir) else f"Não foi possível abrir: {scans_dir}")

        else:
            click.echo("Opção inválida.")

        if not click.confirm("\nExecutar outra ação?", default=True):
            break

    try:
        click.pause(info="\nPressione ENTER para sair...")
    except Exception:
        pass

# registro de comandos para uso direto
cli.add_command(cmd_form)
cli.add_command(cmd_scan)

if __name__ == "__main__":
    cli()
