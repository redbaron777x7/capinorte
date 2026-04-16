"""
Farmaexpress.com — Extrator COMPLETO v3
========================================
ESTRATÉGIA FINAL:
  A API VTEX limita 2.500 produtos por slug.
  Para categorias maiores (Droguería ~4.278, Cuidado Personal ~3.070)
  usamos faixas de preço via parâmetro  fq=P:[min TO max]
  — cada faixa retorna < 2.500 itens, cobrindo 100% do catálogo.

Requisitos:
  pip install requests pandas tqdm

Uso:
  python farmaexpress_v3.py
"""

import requests
import pandas as pd
import json
import time
import sys
from tqdm import tqdm

# ─────────────────────────────────────────────────
BASE_URL  = "https://www.farmaexpress.com"
PAGE_SIZE = 49
DELAY     = 0.6
TIMEOUT   = 25
VTEX_HARD_LIMIT = 2490   # margem de segurança abaixo de 2500

OUTPUT_CSV  = "produtos_co_v3.csv"
OUTPUT_JSON = "produtos_co_v3.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json",
    "Accept-Language": "es-CO,es;q=0.9",
}

# ─────────────────────────────────────────────────
# FAIXAS DE PREÇO (COP) para quebrar categorias grandes
# Cobrindo de $0 até $700.000 COP (máximo visto: $637.500)
# Cada faixa deve ter < 2.500 produtos — ajustadas pelo tamanho
# real de Droguería e Cuidado Personal.
# ─────────────────────────────────────────────────
FAIXAS_PRECO = [
    (0,      9999),
    (10000,  19999),
    (20000,  29999),
    (30000,  44999),
    (45000,  59999),
    (60000,  89999),
    (90000,  149999),
    (150000, 299999),
    (300000, 700000),
]

# ─────────────────────────────────────────────────
# CATEGORIAS
# slug_principal: endpoint base da categoria
# usar_faixas: True = divide por preço (categorias grandes)
# ─────────────────────────────────────────────────
CATEGORIAS = [
    # Grandes — dividir por faixa de preço
    {"nome": "Droguería",        "slug": "/medicamentos/drogueria",   "usar_faixas": True},
    {"nome": "Cuidado Personal", "slug": "/cuidado-personal",         "usar_faixas": True},

    # Normais — slug direto
    {"nome": "Belleza",                    "slug": "/belleza"},
    {"nome": "Mercado y Hogar",            "slug": "/mercado-y-hogar"},
    {"nome": "Cuidado Bebé y Mamá",        "slug": "/cuidado-del-bebe-y-mama"},
    {"nome": "Complementos y Suplementos", "slug": "/medicamentos/complementos-y-suplementos"},
    {"nome": "Productos Naturales",        "slug": "/medicamentos/productos-naturales"},
    {"nome": "Fórmulas Infantiles",        "slug": "/medicamentos/formulas-infantiles"},
    {"nome": "Homeopáticos",               "slug": "/medicamentos/homeopaticos"},
]

# ─────────────────────────────────────────────────
# FUNÇÕES
# ─────────────────────────────────────────────────

def buscar_pagina(slug: str, from_idx: int, to_idx: int,
                  faixa: tuple = None) -> list:
    """Busca uma página. Se faixa=(min,max), adiciona filtro de preço."""
    url = (
        f"{BASE_URL}/api/catalog_system/pub/products/search{slug}"
        f"?_from={from_idx}&_to={to_idx}"
    )
    if faixa:
        url += f"&fq=P:[{faixa[0]} TO {faixa[1]}]"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code in (400, 404):
            return []
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"\n  ⚠️  Erro {slug} [{from_idx}-{to_idx}] faixa={faixa}: {e}")
        return []


def extrair_imagens(produto: dict) -> list:
    urls = []
    for item in produto.get("items", []):
        for img in item.get("images", []):
            url_raw = img.get("imageUrl", "")
            url_hd  = url_raw.split("?")[0] if "?" in url_raw else url_raw
            if url_hd and url_hd not in urls:
                urls.append(url_hd)
    return urls


def extrair_produto(p: dict, categoria: str) -> dict:
    imagens   = extrair_imagens(p)
    descricao = (p.get("description", "") or p.get("metaTagDescription", "")).strip()

    preco = preco_lista = None
    try:
        oferta      = p["items"][0]["sellers"][0]["commertialOffer"]
        preco       = oferta.get("Price")
        preco_lista = oferta.get("ListPrice")
    except (KeyError, IndexError):
        pass

    return {
        "produto_id":      p.get("productId", ""),
        "sku":             p["items"][0].get("itemId", "") if p.get("items") else "",
        "ean":             p["items"][0].get("ean", "")    if p.get("items") else "",
        "nome":            p.get("productName", "").strip(),
        "marca":           p.get("brand", "").strip(),
        "categoria":       categoria,
        "descricao":       descricao,
        "url_produto":     f"{BASE_URL}{p.get('link', '')}",
        "preco_cop":       preco,
        "preco_lista_cop": preco_lista,
        "qtd_imagens":     len(imagens),
        "imagem_1":        imagens[0] if len(imagens) > 0 else "",
        "imagem_2":        imagens[1] if len(imagens) > 1 else "",
        "imagem_3":        imagens[2] if len(imagens) > 2 else "",
        "imagem_4":        imagens[3] if len(imagens) > 3 else "",
        "todas_imagens":   " | ".join(imagens),
    }


def paginar_slug(slug: str, categoria: str, ids_vistos: set,
                 barra: tqdm, faixa: tuple = None) -> list:
    """Pagina um slug (com faixa opcional) e retorna novos produtos."""
    novos  = []
    from_i = 0
    total_na_faixa = 0

    while True:
        to_i  = from_i + PAGE_SIZE
        prods = buscar_pagina(slug, from_i, to_i, faixa)

        if not prods:
            break

        for p in prods:
            pid = p.get("productId", "")
            if pid and pid not in ids_vistos:
                ids_vistos.add(pid)
                novos.append(extrair_produto(p, categoria))
                barra.update(1)
            total_na_faixa += 1

        if len(prods) < PAGE_SIZE + 1:
            break  # última página

        from_i = to_i + 1

        # Segurança: se chegou no limite duro, avisa
        if from_i >= VTEX_HARD_LIMIT:
            print(f"\n  ⚠️  Faixa {faixa} atingiu {VTEX_HARD_LIMIT} — considere dividir mais fino")
            break

        time.sleep(DELAY)

    return novos


def coletar_categoria(cat: dict, ids_vistos: set) -> list:
    slug      = cat["slug"]
    nome      = cat["nome"]
    usar_fxs  = cat.get("usar_faixas", False)
    novos     = []

    barra = tqdm(desc=f"  {nome}", unit=" prod", leave=False, ncols=75)

    if usar_fxs:
        # Divide por faixas de preço para superar o limite de 2.500
        for faixa in FAIXAS_PRECO:
            lote = paginar_slug(slug, nome, ids_vistos, barra, faixa=faixa)
            novos.extend(lote)
            time.sleep(0.4)

        # Passo extra: sem filtro de preço — captura produtos sem preço definido
        lote = paginar_slug(slug, nome, ids_vistos, barra, faixa=None)
        novos.extend(lote)
    else:
        novos = paginar_slug(slug, nome, ids_vistos, barra, faixa=None)

    barra.close()
    return novos


# ─────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────

def main():
    print()
    print("=" * 60)
    print("  Farmaexpress.com — Extrator Completo v3")
    print("  Estratégia: faixas de preço para bypassar limite 2500")
    print("=" * 60)
    print()

    todos      = []
    ids_vistos = set()

    for cat in CATEGORIAS:
        print(f"📦 {cat['nome']}{' (faixas de preço)' if cat.get('usar_faixas') else ''} ...")
        lote = coletar_categoria(cat, ids_vistos)
        todos.extend(lote)
        print(f"   ✅ {len(lote):>5} novos  |  acumulado: {len(todos)}")
        time.sleep(1.0)

    if not todos:
        print("\n❌ Nenhum produto coletado.")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"  Total de produtos únicos: {len(todos)}")
    print(f"{'─'*60}\n")

    # Salvar CSV
    df = pd.DataFrame(todos)
    colunas = [
        "produto_id","sku","ean",
        "nome","marca","categoria","descricao",
        "imagem_1","imagem_2","imagem_3","imagem_4",
        "qtd_imagens","todas_imagens",
        "preco_cop","preco_lista_cop","url_produto",
    ]
    df = df[[c for c in colunas if c in df.columns]]
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"✅ CSV salvo:  {OUTPUT_CSV}")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON salvo: {OUTPUT_JSON}\n")

    # Resumo
    print("📊 Resumo por categoria:")
    resumo = df.groupby("categoria").agg(
        produtos      =("produto_id",  "count"),
        com_descricao =("descricao",   lambda x: (x.str.strip() != "").sum()),
        media_imagens =("qtd_imagens", "mean"),
    ).reset_index()
    resumo["media_imagens"] = resumo["media_imagens"].round(1)
    print(resumo.to_string(index=False))

    sem_desc = (df["descricao"].str.strip() == "").sum()
    sem_img  = (df["imagem_1"] == "").sum()
    print(f"\n⚠️  Sem descrição: {sem_desc:>5} ({sem_desc/len(df)*100:.1f}%)")
    print(f"⚠️  Sem imagem:    {sem_img:>5} ({sem_img/len(df)*100:.1f}%)")
    print("\n🎉 Concluído!")


if __name__ == "__main__":
    main()
