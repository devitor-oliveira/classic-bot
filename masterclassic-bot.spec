# -*- mode: python ; coding: utf-8 -*-

# Spec otimizado para classic-bot (onefile + console + layout src/)
# Observações:
# - 'pathex' equivale a --paths src (garante que os imports em src/ sejam encontrados).  :contentReference[oaicite:1]{index=1}
# - Em one-file NÃO há COLLECT; o EXE recebe tudo (scripts, módulos e binários).       :contentReference[oaicite:2]{index=2}
# - 'excludes' remove dependências opcionais que geram warn e não são usadas aqui.      :contentReference[oaicite:3]{index=3}
# - Se seu ambiente tiver /tmp com noexec, prefira rodar com TMPDIR=... ou gerar onedir
#   (ou defina runtime_tmpdir para um caminho ABSOLUTO específico da máquina).          :contentReference[oaicite:4]{index=4}

block_cipher = None

a = Analysis(
    ['launcher_cli.py'],
    pathex=['src'],
    binaries=[],
    datas=[],              # se um dia precisar embutir assets, use datas=[('src/...','dest')]
    hiddenimports=[],      # adicione aqui se houver imports dinâmicos
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'IPython',
        'dotenv.ipython',
        'OpenSSL',
        'cryptography',
        'h2',
        'brotli',
        'brotlicffi',
        'zstandard',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='masterclassic-bot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,              # requer UPX instalado; se não tiver, mantenha True (só gera aviso). :contentReference[oaicite:5]{index=5}
    upx_exclude=[],
    runtime_tmpdir=None,   # deixe None (padrão). Se precisar contornar /tmp noexec, use --runtime-tmpdir em CLI. :contentReference[oaicite:6]{index=6}
    console=True,          # mantém o terminal (menu interativo)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
