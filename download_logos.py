"""
Script para baixar logos das marcas farmacêuticas
Salva em static/img/brands/
"""
import os, urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

os.makedirs("static/img/brands", exist_ok=True)

# Lista de (nome_arquivo, url_logo)
# Usando fontes confiáveis: CDN da Wikimedia, sites oficiais, clearbit
logos = [
    ("engystol.png",       "https://upload.wikimedia.org/wikipedia/commons/thumb/7/74/Heel_logo.svg/320px-Heel_logo.svg.png"),
    ("electrolit.png",     "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Electrolit_logo.svg/320px-Electrolit_logo.svg.png"),
    ("allegra.png",        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Sanofi_logo.svg/320px-Sanofi_logo.svg.png"),
    ("enterogermina.png",  "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Sanofi_logo.svg/320px-Sanofi_logo.svg.png"),
    ("ponds.png",          "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Pond%27s_logo.svg/320px-Pond%27s_logo.svg.png"),
    ("nivea.png",          "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Nivea_logo.svg/320px-Nivea_logo.svg.png"),
    ("eucerin.png",        "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Eucerin_logo.svg/320px-Eucerin_logo.svg.png"),
    ("bayer.png",          "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/Bayer_AG_logo.svg/320px-Bayer_AG_logo.svg.png"),
    ("sanofi.png",         "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Sanofi_logo.svg/320px-Sanofi_logo.svg.png"),
    ("genfar.png",         "https://logo.clearbit.com/genfar.com"),
    ("procaps.png",        "https://logo.clearbit.com/procaps.com.co"),
    ("novartis.png",       "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/Novartis-Logo.svg/320px-Novartis-Logo.svg.png"),
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for fname, url in logos:
    dest = f"static/img/brands/{fname}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        print(f"✅ {fname} ({len(data)} bytes)")
    except Exception as e:
        print(f"❌ {fname}: {e}")

print("\nDone!")
