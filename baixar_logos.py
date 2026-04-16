#!/usr/bin/env python3
"""Baixa logos reais das marcas da pasta brands."""
import os, urllib.request, urllib.error, ssl

DEST = r"C:\Users\Home\Desktop\Capi copia\static\img\brands"
os.makedirs(DEST, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

# Lista: (arquivo_destino, [lista_urls_tentativa])
LOGOS = [
    ("engystol.png", [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b4/Engystol_logo.svg/500px-Engystol_logo.svg.png",
        "https://www.heel.com/fileadmin/user_upload/Heel_Logo_4c.png",
        "https://seeklogo.com/images/E/engystol-logo-B4C4C5D4E3-seeklogo.com.png",
    ]),
    ("Enterogermina.png", [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Enterogermina_logo.svg/500px-Enterogermina_logo.svg.png",
        "https://www.enterogermina.com.co/sites/g/files/vrxlpx36226/files/logo.png",
        "https://logowik.com/content/uploads/images/enterogermina1823.jpg",
        "https://1000marcas.net/wp-content/uploads/2022/09/Enterogermina-Logo.png",
    ]),
    ("Ponds.png", [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Pond%27s_logo.svg/500px-Pond%27s_logo.svg.png",
        "https://1000marcas.net/wp-content/uploads/2020/02/Ponds-Logo.png",
        "https://logowik.com/content/uploads/images/ponds1878.jpg",
    ]),
    ("nivea.png", [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fb/Nivea_logo.svg/500px-Nivea_logo.svg.png",
        "https://1000marcas.net/wp-content/uploads/2020/02/Nivea-Logo.png",
        "https://logowik.com/content/uploads/images/nivea4437.jpg",
    ]),
    ("Eucerin.png", [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Eucerin_Logo.svg/500px-Eucerin_Logo.svg.png",
        "https://1000marcas.net/wp-content/uploads/2022/09/Eucerin-Logo.png",
        "https://logowik.com/content/uploads/images/eucerin6977.jpg",
    ]),
    ("Genfar.png", [
        "https://www.genfar.com.co/themes/custom/genfar/images/logo.svg",
        "https://seeklogo.com/images/G/genfar-logo-D2C4C7E5A6-seeklogo.com.png",
        "https://logowik.com/content/uploads/images/genfar4621.jpg",
        "https://1000marcas.net/wp-content/uploads/2021/10/Genfar-Logo.png",
    ]),
    ("lasante.png", [
        "https://www.lasante.com.co/wp-content/themes/lasante/img/logo.png",
        "https://seeklogo.com/images/L/la-sante-logo-E3C5E5E3A4-seeklogo.com.png",
        "https://logowik.com/content/uploads/images/la-sante7289.jpg",
    ]),
    ("mk.png", [
        "https://www.laboratoriosmk.com/wp-content/uploads/logo-mk.png",
        "https://seeklogo.com/images/M/mk-laboratorios-logo-A3B3C5D2E1-seeklogo.com.png",
        "https://1000marcas.net/wp-content/uploads/2021/10/MK-Laboratorios-Logo.png",
        "https://logowik.com/content/uploads/images/mk-laboratorios5432.jpg",
    ]),
]

def download(url, dest_path):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        data = r.read()
    if len(data) < 1000:
        raise ValueError(f"Arquivo muito pequeno ({len(data)} bytes), provavelmente erro")
    with open(dest_path, "wb") as f:
        f.write(data)
    return len(data)

print("=== Baixando logos das marcas ===\n")
results = {}
for filename, urls in LOGOS:
    dest = os.path.join(DEST, filename)
    ok = False
    for url in urls:
        try:
            size = download(url, dest)
            print(f"✅ {filename} — OK ({size:,} bytes)\n   URL: {url}")
            results[filename] = "ok"
            ok = True
            break
        except Exception as e:
            print(f"   ❌ Falhou: {url}\n      {e}")
    if not ok:
        print(f"⚠️  {filename} — NENHUMA URL funcionou")
        results[filename] = "falhou"

print("\n=== RESUMO ===")
for f, s in results.items():
    print(f"  {'✅' if s=='ok' else '❌'} {f}: {s}")
