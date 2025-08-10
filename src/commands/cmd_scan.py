# -*- coding: utf-8 -*-
"""
Comando: scan
- Solicita URL (ou usa --url)
- Abre a página e varre elementos relevantes (inputs, selects, textareas, buttons, a, label, [role=button], [data-testid])
- Coleta atributos (id, name, type, placeholder, href, class, data-testid, aria-label, role, text)
- Gera candidatos de seletores (CSS) e verifica se são únicos via querySelectorAll
- Salva JSON + HTML em Documentos/classicbot/scans e abre o HTML no navegador
"""

from __future__ import annotations
import json
import time
import logging
from pathlib import Path
import click

from selenium.webdriver.support.ui import WebDriverWait

from utils.paths import classicbot_dirs
from utils.driver_factory import create_chrome_driver

log = logging.getLogger("cmd_scan")

def _wait_ready(driver, timeout=20):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")

@click.command(name="scan", help="Faz o inventário de elementos de uma página e gera JSON + HTML em 'scans'.")
@click.option("--url", prompt=True, help="URL da página a escanear.")
@click.option("--headed", is_flag=True, help="Executa com interface gráfica (sem headless).")
def cmd_scan(url: str, headed: bool):
    dirs = classicbot_dirs()
    scans_dir = dirs["scans"]
    scans_dir.mkdir(parents=True, exist_ok=True)

    driver = None
    try:
        driver = create_chrome_driver(headless=not headed)
        driver.set_page_load_timeout(60)
        driver.get(url)
        _wait_ready(driver)

        # Screenshot da página
        ts = int(time.time() * 1000)
        shot = scans_dir / f"scan_{ts}.png"
        try:
            driver.save_screenshot(str(shot))
        except Exception:
            pass

        # JS: coleta elementos + candidatos de seletores e verifica unicidade
        script = r"""
return (function(){
  function cssEsc(s){return (window.CSS && CSS.escape)? CSS.escape(s): String(s).replace(/([#.;:[\]()>+~*^$|=])/g,'\\$1');}
  function getCandidates(el){
    const tag = el.tagName.toLowerCase();
    let c = [];
    const id = el.getAttribute('id');
    if (id) c.push('#'+cssEsc(id));
    const testid = el.getAttribute('data-testid');
    if (testid) c.push(`[data-testid="${cssEsc(testid)}"]`);
    const name = el.getAttribute('name');
    if (name) c.push(`${tag}[name="${cssEsc(name)}"]`);
    const aria = el.getAttribute('aria-label');
    if (aria) c.push(`[aria-label="${cssEsc(aria)}"]`);
    if ((tag==='input'||tag==='textarea')){
      const ph = el.getAttribute('placeholder');
      if (ph) c.push(`${tag}[placeholder="${cssEsc(ph)}"]`);
      const tp = el.getAttribute('type');
      if (tp) c.push(`input[type="${cssEsc(tp)}"]`);
    }
    if (tag==='a'){
      const href = el.getAttribute('href');
      if (href){
        const short = href.replace(/^https?:\/\/[^/]+/,'');
        if (short) {
          c.push(`a[href="${cssEsc(short)}"]`);
          c.push(`a[href*="${cssEsc(short.slice(0,40))}"]`);
        }
      }
    }
    const cls = (el.getAttribute('class')||'').trim();
    if (cls){
      const parts = cls.split(/\s+/).map(x=>'.'+cssEsc(x)).join('');
      c.push(tag+parts);
    }
    function nthPath(e){
      let path=[];
      let depth=0;
      while(e && e.nodeType===1 && depth<5){
        const id=e.getAttribute('id');
        if (id){ path.unshift('#'+cssEsc(id)); break; }
        const t=e.tagName.toLowerCase();
        let i=1, sib=e;
        while((sib=sib.previousElementSibling)!=null){ if (sib.tagName.toLowerCase()===t) i++; }
        path.unshift(`${t}:nth-of-type(${i})`);
        e=e.parentElement; depth++;
      }
      return path.join(' > ');
    }
    c.push(nthPath(el));
    // dedup
    return Array.from(new Set(c.filter(Boolean)));
  }
  function isUnique(sel){
    try { return document.querySelectorAll(sel).length===1; } catch(e){ return false; }
  }
  function shortText(el){
    const t=(el.textContent||'').trim().replace(/\s+/g,' ');
    return t.length>120? t.slice(0,117)+'…': t;
  }
  const nodes = Array.from(document.querySelectorAll(
    'input, select, textarea, button, a, label, [role=\"button\"], [data-testid]'
  ));
  return nodes.map(el=>{
    const tag = el.tagName.toLowerCase();
    const attrs = {};
    ['id','name','type','placeholder','href','class','data-testid','aria-label','role','value']
      .forEach(k=>{ const v=el.getAttribute(k); if(v!=null) attrs[k]=v; });
    const candidates = getCandidates(el).map(s=>({selector:s, unique:isUnique(s)}));
    return { tag, text: shortText(el), attributes: attrs, candidates };
  });
})();"""
        elements = driver.execute_script(script)  # Selenium execute_script (API oficial) 
        count = len(elements)

        # Salva JSON
        payload = {
            "scanned_at": ts,
            "url": url,
            "screenshot": str(shot.name),
            "count": count,
            "elements": elements
        }
        json_path = scans_dir / f"scan_{ts}.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        # Gera HTML simples e amigável
        rows = []
        for idx, el in enumerate(elements, 1):
            attrs = el.get("attributes", {})
            cand_rows = "".join(
                f"<li><code>{c['selector']}</code> — {'único ✅' if c.get('unique') else 'múltiplo ❌'}</li>"
                for c in el.get("candidates", [])
            )
            rows.append(f"""
<tr>
  <td style="border:1px solid #e5e7eb;padding:8px">{idx}</td>
  <td style="border:1px solid #e5e7eb;padding:8px">{el.get('tag','')}</td>
  <td style="border:1px solid #e5e7eb;padding:8px">{(attrs.get('id','') or '')}</td>
  <td style="border:1px solid #e5e7eb;padding:8px">{(attrs.get('name','') or '')}</td>
  <td style="border:1px solid #e5e7eb;padding:8px">{(attrs.get('placeholder','') or attrs.get('aria-label','') or '')}</td>
  <td style="border:1px solid #e5e7eb;padding:8px">{el.get('text','')}</td>
  <td style="border:1px solid #e5e7eb;padding:8px"><details><summary>ver seletores</summary><ul>{cand_rows}</ul></details></td>
</tr>""")
        html_doc = f"""<!doctype html>
<meta charset="utf-8">
<title>Scan de elementos — classicbot</title>
<body style="font-family:system-ui,Segoe UI,Arial;margin:24px;max-width:1100px">
  <h1 style="margin:0 0 8px">Scan de elementos</h1>
  <p style="margin:0 0 6px;color:#334155">URL: {url}</p>
  <p style="margin:0 0 16px;color:#334155">Total de elementos mapeados: <b>{count}</b></p>
  <p style="margin:0 0 16px"><img alt="screenshot" src="{shot.name}" style="max-width:100%;border:1px solid #e5e7eb;border-radius:8px"></p>
  <table style="border-collapse:collapse;width:100%">
    <thead>
      <tr style="background:#f1f5f9">
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">#</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">tag</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">id</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">name</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">placeholder/aria</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">texto</th>
        <th style="text-align:left;padding:8px;border:1px solid #e5e7eb">seletores</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <p style="margin-top:24px;color:#64748b">Gerado automaticamente pelo classic-bot.</p>
</body>"""
        html_path = scans_dir / f"scan_{ts}.html"
        html_path.write_text(html_doc, encoding="utf-8")

        # Abre HTML no navegador
        import webbrowser
        try:
            webbrowser.open(html_path.resolve().as_uri())
        except Exception:
            pass

        click.echo(f"✅ SCAN salvo em:\n  HTML: {html_path}\n  JSON: {json_path}\n  Screenshot: {shot}")
        return 0

    except Exception as e:
        click.echo(f"❌ Falha no SCAN: {e}")
        log.exception("Falha no SCAN: %s", e)
        return 1

    finally:
        if driver:
            driver.quit()
