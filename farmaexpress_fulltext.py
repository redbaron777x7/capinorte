"""
farmaexpress_fulltext.py — Captura produtos perdidos via busca full-text
========================================================================
Usa o endpoint de busca da VTEX (?_q=TERMO&map=ft) para encontrar
produtos que não aparecem nas categorias padrão.

Estratégia: busca por cada letra A-Z + termos comuns de medicamentos
Resultado: merge com o CSV existente, adicionando apenas os novos.

Uso:
  python farmaexpress_fulltext.py
  python farmaexpress_fulltext.py --merge produtos_co_v3.csv
"""

import requests
import pandas as pd
import json
import time
import sys
import argparse
from tqdm import tqdm

BASE_URL  = "https://www.farmaexpress.com"
PAGE_SIZE = 49
DELAY     = 0.5
TIMEOUT   = 20

OUTPUT_CSV  = "produtos_fulltext.csv"
OUTPUT_JSON = "produtos_fulltext.json"
MERGED_CSV  = "produtos_final.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "es-CO,es;q=0.9",
}

# ── Termos de busca ──────────────────────────────────────────
# Letras A-Z (captura todos os produtos pelo nome)
LETRAS = list("abcdefghijklmnopqrstuvwxyz")

# Termos específicos de medicamentos comuns na Colômbia
TERMOS_EXTRA = [
    "buscapina", "dolex", "acetaminofen", "ibuprofeno", "amoxicilina",
    "metformina", "losartan", "omeprazol", "atorvastatina", "aspirina",
    "clonazepam", "diclofenaco", "naproxeno", "ranitidina", "sildenafil",
    "tadalafil", "ciprofloxacino", "azitromicina", "doxiciclina", "cetirizina",
    "loratadina", "betametasona", "hidrocortisona", "prednisona", "insulina",
    "furosemida", "espironolactona", "enalapril", "amlodipino", "metoprolol",
    "vitamina", "calcio", "hierro", "magnesio", "zinc", "omega",
    "collagen", "biotina", "melatonina", "probiotico", "lactobacilo",
    "crema", "jarabe", "suspension", "ampolla", "capsula", "tableta",
    "gotas", "solucion", "pomada", "gel", "parche", "inyectable",
    "pediatrico", "infantil", "adulto", "geriatrico",
    "genfar", "lafrancol", "procaps", "tecnoquimicas", "pfizer",
    "bayer", "novartis", "sanofi", "roche", "abbott",
]

# Remove duplicatas e ordena
TODOS_TERMOS = list(dict.fromkeys(LETRAS + TERMOS_EXTRA))

# ─────────────────────────────────────────────────────────────

def buscar_fulltext(termo: str, from_idx: int, to_idx: int) -> list:
    """Busca full-text na API VTEX."""
    url = (
        f"{BASE_URL}/api/catalog_system/pub/products/search"
        f"?_q={requests.utils.quote(termo)}&map=ft"
        f"&_from={from_idx}&_to={to_idx}"
    )
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code in (400, 404, 429):
            return []
        r.raise_for_status()
        return r.json()
    except Exception:
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


def extrair_produto(p: dict) -> dict:
    imagens   = extrair_imagens(p)
    descricao = (p.get("description","") or p.get("metaTagDescription","")).strip()

    # Categoria do produto (path VTEX)
    cats = p.get("categories", [])
    categoria = ""
    if cats:
        # Pega a categoria mais específica (última do path)
        categoria = cats[0].strip("/").split("/")[-1] if cats else ""

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


def coletar_termo(termo: str, ids_vistos: set, barra_global) -> list:
    """Pagina um termo de busca e retorna produtos novos."""
    novos  = []
    from_i = 0

    while from_i < 2490:  # limite VTEX
        to_i  = from_i + PAGE_SIZE
        prods = buscar_fulltext(termo, from_i, to_i)

        if not prods:
            break

        for p in prods:
            pid = p.get("productId", "")
            if pid and pid not in ids_vistos:
                ids_vistos.add(pid)
                novos.append(extrair_produto(p))
                barra_global.update(1)

        if len(prods) < PAGE_SIZE + 1:
            break

        from_i = to_i + 1
        time.sleep(DELAY)

    return novos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--merge", help="CSV existente para fazer merge", default=None)
    args = parser.parse_args()

    print()
    print("=" * 62)
    print("  Farmaexpress — Captura Full-Text (produtos perdidos)")
    print("=" * 62)

    # Carregar IDs já existentes (evita duplicar)
    ids_vistos = set()
    df_existente = None

    if args.merge:
        try:
            df_existente = pd.read_csv(args.merge, encoding="utf-8-sig", low_memory=False)
            ids_existentes = set(df_existente["produto_id"].dropna().astype(str).tolist())
            ids_vistos.update(ids_existentes)
            print(f"📂 CSV existente carregado: {len(df_existente)} produtos")
            print(f"   IDs já conhecidos: {len(ids_vistos)}")
        except Exception as e:
            print(f"  ⚠️  Não foi possível carregar {args.merge}: {e}")

    print(f"\n🔍 Buscando por {len(TODOS_TERMOS)} termos...")
    print("   (isso pode demorar ~15-20 minutos)\n")

    todos_novos = []
    barra = tqdm(desc="Novos produtos", unit=" prod", position=0, leave=True)
    barra_termos = tqdm(total=len(TODOS_TERMOS), desc="Termos", unit=" termo",
                        position=1, leave=True)

    for termo in TODOS_TERMOS:
        novos = coletar_termo(termo, ids_vistos, barra)
        todos_novos.extend(novos)
        barra_termos.update(1)
        barra_termos.set_postfix({"novo": len(todos_novos), "termo": termo})
        time.sleep(DELAY)

    barra.close()
    barra_termos.close()

    print(f"\n✅ {len(todos_novos)} produtos NOVOS encontrados (não estavam no CSV anterior)")

    if not todos_novos and not df_existente is not None:
        print("Nenhum produto novo encontrado.")
        return

    # Salvar só os novos
    df_novos = pd.DataFrame(todos_novos)
    if not df_novos.empty:
        df_novos.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"✅ Novos salvos em: {OUTPUT_CSV}")

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(todos_novos, f, ensure_ascii=False, indent=2)

    # Merge com o existente
    if df_existente is not None and not df_novos.empty:
        df_final = pd.concat([df_existente, df_novos], ignore_index=True)
        df_final.to_csv(MERGED_CSV, index=False, encoding="utf-8-sig")
        print(f"\n🔗 CSV FINAL (merge): {MERGED_CSV}")
        print(f"   Antes:  {len(df_existente):>6} produtos")
        print(f"   Novos:  {len(df_novos):>6} produtos")
        print(f"   Total:  {len(df_final):>6} produtos")
        print(f"\n▶  Importe o CSV final: python importar_csv.py {MERGED_CSV}")
    elif df_existente is not None and df_novos.empty:
        print("\n✅ Nenhum produto novo — seu CSV já está completo!")
    else:
        print(f"\n▶  Importe: python importar_csv.py {OUTPUT_CSV}")

    print("\n🎉 Concluído!")


if __name__ == "__main__":
    main()
