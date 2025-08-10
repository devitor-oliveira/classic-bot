# -*- coding: utf-8 -*-
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import json
import webbrowser
import html

@dataclass
class Step:
    name: str
    status: str  # "pass" | "fail" | "info"
    message: str = ""
    screenshot: str = ""  # relativo à pasta HTML

class HTMLReporter:
    def __init__(self, out_dir: Path, json_out_dir: Path | None = None):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.json_out_dir = Path(json_out_dir) if json_out_dir else self.out_dir
        self.json_out_dir.mkdir(parents=True, exist_ok=True)

        self.steps: list[Step] = []
        self.meta = {"started_at": datetime.now().isoformat(timespec="seconds")}

    def add_step(self, name, status="info", message="", screenshot=""):
        self.steps.append(Step(name, status, message, screenshot))

    def save(self, open_in_browser: bool = True):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON “humano” + útil pra CI
        json_payload = {"meta": self.meta, "steps": [asdict(s) for s in self.steps]}
        json_file = self.json_out_dir / f"{ts}_report.json"
        json_file.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        # HTML amigável
        rows = []
        for s in self.steps:
            badge = {"pass": "#16a34a", "fail": "#dc2626", "info": "#2563eb"}.get(s.status, "#2563eb")
            shot = f'<a href="{html.escape(s.screenshot)}" target="_blank">ver</a>' if s.screenshot else ""
            rows.append(f"""
              <tr>
                <td style="padding:8px;border:1px solid #e5e7eb">{html.escape(s.name)}</td>
                <td style="padding:8px;border:1px solid #e5e7eb">
                  <span style="background:{badge};color:#fff;padding:3px 8px;border-radius:999px;text-transform:uppercase;font:12px/1 system-ui">{s.status}</span>
                </td>
                <td style="padding:8px;border:1px solid #e5e7eb">{html.escape(s.message)}</td>
                <td style="padding:8px;border:1px solid #e5e7eb">{shot}</td>
              </tr>""")
        html_doc = f"""<!doctype html>
<html lang="pt-br"><meta charset="utf-8">
<title>Relatório de Testes - masterClassic</title>
<body style="font-family:system-ui,Segoe UI,Arial;margin:24px;max-width:980px">
  <h1 style="margin:0 0 8px">Relatório de Testes</h1>
  <p style="margin:0 0 16px;color:#475569">Início: {self.meta['started_at']}</p>
  <table style="border-collapse:collapse;width:100%">
    <thead>
      <tr style="background:#f1f5f9">
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">Passo</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">Status</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">Mensagem</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">Screenshot</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <p style="margin-top:24px;color:#475569">Gerado automaticamente pelo classic-bot.</p>
</body></html>"""
        html_file = self.out_dir / f"{ts}_report.html"
        html_file.write_text(html_doc, encoding="utf-8")

        # conveniência: ponteiros “latest”
        try:
            (self.out_dir / "latest_report.html").write_text(html_doc, encoding="utf-8")
            (self.json_out_dir / "latest_report.json").write_text(
                json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception:
            pass

        if open_in_browser:
            try:
                webbrowser.open(html_file.resolve().as_uri())
            except Exception:
                pass

        return html_file, json_file
