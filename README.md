classic-bot (masterClassic QA CLI)

CLI em Python para testar o site masterclassic.com.br com Selenium.
Inclui menu interativo (Click), relatório HTML/JSON com screenshots e um scanner de página para sugerir seletores.
Pronto para empacotar com PyInstaller (Windows e Linux).

    Documentação do Selenium para recursos usados (esperas explícitas, Select, Selenium Manager) e do PyInstaller estão referenciadas no final deste README.

Pré-requisitos

    Python 3.10+

    Google Chrome instalado (ou outro navegador compatível).

    (Dev) virtualenv recomendado.

Como rodar em modo dev (sem empacotar)
Windows (PowerShell)

py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python launcher_cli.py

Linux

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python launcher_cli.py

Build com PyInstaller

    Importante: gere o executável no próprio sistema de destino (Windows → .exe no Windows; Linux → binário no Linux).

Windows (.exe)

.\.venv\Scripts\activate
pip install pyinstaller
pyinstaller --onefile --console --name masterclassic-bot --paths src launcher_cli.py
# executa
dist\masterclassic-bot.exe

Linux (binário)

source .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --console --name masterclassic-bot --paths src launcher_cli.py
# executa
./dist/masterclassic-bot

Dica (Linux): se o binário one-file não abrir por políticas de execução temporária, rode com TMP alternativo:

mkdir -p "$HOME/tmp"
TMPDIR="$HOME/tmp" ./dist/masterclassic-bot

ou gere em --onedir se preferir distribuir uma pasta.
Troubleshooting

    Warn de “missing modules” no build: muitos itens são opcionais ou específicos de outro SO (ex.: winreg no Linux). Só aja se aparecer erro em runtime — então adicione o pacote, use --hidden-import ou exclua módulos que você não utiliza.

    Demora na 1ª execução do one-file: é a extração inicial (comportamento esperado).

    Sincronização Selenium: priorize WebDriverWait + expected conditions em vez de sleep fixo.

Contribuindo

    Crie uma branch a partir de main.

    Faça commits pequenos e mensagens claras.

    Abra um Pull Request descrevendo as mudanças.

Licença

Este projeto está licenciado sob a GNU General Public License v3.0 (GPL-3.0).
Consulte o arquivo LICENSE na raiz do repositório para o texto completo.
Referências

    Selenium – Expected Conditions (inclui url_contains, url_changes) e WebDriverWait.
    Selenium+2Selenium+2

    Selenium – Select lists (Select para <select>).
    Selenium

    Selenium – Selenium Manager (dispensa baixar driver manual).
    Selenium+1

    PyInstaller – uso geral, --paths, --runtime-tmpdir, .spec.
    pyin
