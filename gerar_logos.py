# Gera logos SVG texto para cada marca farmacêutica
# Baseado nas identidades oficiais de cada marca
import os

os.makedirs("static/img/brands", exist_ok=True)

logos = {
    "engystol.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="30" font-family="Georgia,serif" font-size="13" fill="#003087" text-anchor="middle" font-weight="bold">biologische</text>
  <text x="100" y="52" font-family="Georgia,serif" font-size="24" fill="#003087" text-anchor="middle" font-weight="bold">Heel</text>
  <text x="100" y="70" font-family="Arial,sans-serif" font-size="11" fill="#666" text-anchor="middle">Engystol</text>
</svg>""",

    "electrolit.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <rect x="10" y="28" width="180" height="26" rx="4" fill="#00539B"/>
  <text x="100" y="47" font-family="Arial Black,Arial,sans-serif" font-size="20" fill="#fff" text-anchor="middle" font-weight="900" letter-spacing="1">Electrolit</text>
</svg>""",

    "allegra.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="54" font-family="Arial,sans-serif" font-size="36" fill="#C8102E" text-anchor="middle" font-weight="bold" font-style="italic">allegra</text>
</svg>""",

    "enterogermina.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="34" font-family="Arial,sans-serif" font-size="13" fill="#E4002B" text-anchor="middle" font-weight="bold">entero</text>
  <text x="100" y="58" font-family="Arial,sans-serif" font-size="13" fill="#E4002B" text-anchor="middle" font-weight="bold">germina</text>
  <circle cx="100" cy="46" r="4" fill="#E4002B"/>
</svg>""",

    "ponds.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="28" font-family="Georgia,serif" font-size="11" fill="#8B6914" text-anchor="middle" letter-spacing="4">POND'S</text>
  <line x1="30" y1="36" x2="170" y2="36" stroke="#8B6914" stroke-width="0.8"/>
  <text x="100" y="60" font-family="Georgia,serif" font-size="20" fill="#5C4633" text-anchor="middle" font-style="italic">Institute</text>
</svg>""",

    "nivea.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <rect x="20" y="20" width="160" height="42" rx="21" fill="#003087"/>
  <text x="100" y="48" font-family="Arial Black,Arial,sans-serif" font-size="24" fill="#fff" text-anchor="middle" font-weight="900" letter-spacing="3">NIVEA</text>
</svg>""",

    "eucerin.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="52" font-family="Arial,sans-serif" font-size="28" fill="#004B87" text-anchor="middle" font-weight="bold" letter-spacing="2">Eucerin</text>
</svg>""",

    "bayer.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <!-- Bayer cross simplified -->
  <rect x="88" y="18" width="24" height="8" rx="2" fill="#10384F"/>
  <rect x="88" y="36" width="24" height="8" rx="2" fill="#10384F"/>
  <rect x="80" y="26" width="8" height="8" rx="2" fill="#10384F"/>
  <rect x="112" y="26" width="8" height="8" rx="2" fill="#10384F"/>
  <text x="100" y="70" font-family="Arial,sans-serif" font-size="16" fill="#10384F" text-anchor="middle" font-weight="bold" letter-spacing="3">BAYER</text>
</svg>""",

    "sanofi.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <!-- Simplified Sanofi purple -->
  <text x="100" y="52" font-family="Arial,sans-serif" font-size="30" fill="#7B2D8B" text-anchor="middle" font-weight="bold" letter-spacing="1">sanofi</text>
</svg>""",

    "genfar.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="52" font-family="Arial Black,Arial,sans-serif" font-size="26" fill="#E4002B" text-anchor="middle" font-weight="900" letter-spacing="1">GENFAR</text>
</svg>""",

    "procaps.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <!-- Procaps orange -->
  <text x="100" y="52" font-family="Arial Black,Arial,sans-serif" font-size="22" fill="#E8641E" text-anchor="middle" font-weight="900" letter-spacing="1">PROCAPS</text>
</svg>""",

    "novartis.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 80">
  <rect width="200" height="80" fill="#fff" rx="8"/>
  <text x="100" y="52" font-family="Arial,sans-serif" font-size="24" fill="#0460A9" text-anchor="middle" font-weight="bold" letter-spacing="1">Novartis</text>
</svg>""",
}

for fname, svg in logos.items():
    path = f"static/img/brands/{fname}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"✅ {fname}")

print("\nDone! All SVG logos created.")
