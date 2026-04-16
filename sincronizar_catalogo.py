"""
sincronizar_catalogo.py — Sincronização incremental do catálogo
================================================================
Verifica se há produtos NOVOS no farmaexpress.com e insere
apenas os que ainda não existem no banco de dados local.

Funciona em 3 etapas:
  1. Busca todos os produto_id atuais no site (rápido, sem baixar dados)
  2. Compara com os IDs já no banco/CSV
  3. Baixa e insere SOMENTE os novos

Uso:
  python sincronizar_catalogo.py              (compara com banco SQLite)
  python sincronizar_catalogo.py --csv        (compara com CSV existente)
  python sincronizar_catalogo.py --forcar     (re-importa tudo)

Requisitos:
  pip install requests pandas tqdm
"""

import requests
import pandas as pd
import sqlite3
import json
import time
import sys
import argparse
from datetime import datetime
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────
BASE_URL   = "https://www.farmaexpress.com"
DB_PATH    = "farmacia/farmacia.db"
CSV_SAIDA  = "produtos_novos.csv"
PAGE_SIZE  = 49
DELAY      = 0.6
TIMEOUT    = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "es-CO,es;q=0.9",
}

# Faixas de preço para categorias grandes (evita limite 2500)
FAIXAS_PRECO = [
    (0, 9999), (10000, 19999), (20000, 29999),
    (30000, 44999), (45000, 59999), (60000, 89999),
    (90000, 149999), (150000, 299999), (300000, 700000),
]

CATEGORIAS = [
    {"nome": "Droguería",                  "slug": "/medicamentos/drogueria",              "faixas": True},
    {"nome": "Cuidado Personal",           "slug": "/cuidado-personal",                    "faixas": True},
    {"nome": "Belleza",                    "slug": "/belleza",                             "faixas": False},
    {"nome": "Mercado y Hogar",            "slug": "/mercado-y-hogar",                     "faixas": False},
    {"nome": "Cuidado Bebé y Mamá",        "slug": "/cuidado-del-bebe-y-mama",             "faixas": False},
    {"nome": "Complementos y Suplementos", "slug": "/medicamentos/complementos-y-suplementos", "faixas": False},
    {"nome": "Productos Naturales",        "slug": "/medicamentos/productos-naturales",    "faixas": False},
    {"nome": "Fórmulas Infantiles",        "slug": "/medicamentos/formulas-infantiles",    "faixas": False},
    {"nome": "Homeopáticos",               "slug": "/medicamentos/homeopaticos",           "faixas": False},
]

# Termos de busca full-text extra
TERMOS_FT = [
    "buscapina","dolex","acetaminofen","ibuprofeno","amoxicilina",
    "metformina","losartan","omeprazol","atorvastatina","aspirina",
    "naproxeno","sildenafil","tadalafil","cetirizina","loratadina",
    "vitamina","calcio","hierro","magnesio","omega","probiotico",
    "genfar","lafrancol","procaps","bayer","novartis","sanofi",
] + list("abcdefghijklmnopqrstuvwxyz")


# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE BUSCA
# ─────────────────────────────────────────────────────────────

def buscar_pagina(slug: str, from_i: int, to_i: int, faixa=None) -> list:
    url = (
        f"{BASE_URL}/api/catalog_system/pub/products/search{slug}"
        f"?_from={from_i}&_to={to_i}"
    )
    if faixa:
        url += f"&fq=P:[{faixa[0]} TO {faixa[1]}]"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code in (400, 404, 429):
            return []
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


def buscar_fulltext(termo: str, from_i: int, to_i: int) -> list:
    url = (
        f"{BASE_URL}/api/catalog_system/pub/products/search"
        f"?_q={requests.utils.quote(termo)}&map=ft"
        f"&_from={from_i}&_to={to_i}"
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
            raw = img.get("imageUrl", "")
            hd  = raw.split("?")[0] if "?" in raw else raw
            if hd and hd not in urls:
                urls.append(hd)
    return urls


def extrair_produto(p: dict, categoria: str) -> dict:
    imgs      = extrair_imagens(p)
    descricao = (p.get("description","") or p.get("metaTagDescription","")).strip()
    preco = preco_lista = None
    try:
        o = p["items"][0]["sellers"][0]["commertialOffer"]
        preco, preco_lista = o.get("Price"), o.get("ListPrice")
    except (KeyError, IndexError):
        pass
    return {
        "produto_id":      p.get("productId",""),
        "sku":             p["items"][0].get("itemId","") if p.get("items") else "",
        "ean":             p["items"][0].get("ean","")    if p.get("items") else "",
        "nome":            p.get("productName","").strip(),
        "marca":           p.get("brand","").strip(),
        "categoria":       categoria,
        "descricao":       descricao,
        "url_produto":     f"{BASE_URL}{p.get('link','')}",
        "preco_cop":       preco,
        "preco_lista_cop": preco_lista,
        "qtd_imagens":     len(imgs),
        "imagem_1":        imgs[0] if len(imgs)>0 else "",
        "imagem_2":        imgs[1] if len(imgs)>1 else "",
        "imagem_3":        imgs[2] if len(imgs)>2 else "",
        "imagem_4":        imgs[3] if len(imgs)>3 else "",
        "todas_imagens":   " | ".join(imgs),
    }


# ─────────────────────────────────────────────────────────────
# COLETA IDs EXISTENTES
# ─────────────────────────────────────────────────────────────

def ids_do_banco() -> set:
    """Carrega todos os produto_id já no banco SQLite."""
    try:
        db = sqlite3.connect(DB_PATH)
        rows = db.execute("SELECT produto_id FROM produtos WHERE produto_id != ''").fetchall()
        db.close()
        ids = {str(r[0]) for r in rows if r[0]}
        print(f"  Banco SQLite: {len(ids)} produtos já cadastrados")
        return ids
    except Exception as e:
        print(f"  ⚠️  Não foi possível ler o banco: {e}")
        return set()


def ids_do_csv(caminho: str) -> set:
    """Carrega produto_ids de um CSV existente."""
    try:
        df = pd.read_csv(caminho, encoding="utf-8-sig", low_memory=False,
                         usecols=["produto_id"])
        ids = set(df["produto_id"].dropna().astype(str).tolist())
        print(f"  CSV {caminho}: {len(ids)} produtos já existentes")
        return ids
    except Exception as e:
        print(f"  ⚠️  Erro ao ler CSV: {e}")
        return set()


# ─────────────────────────────────────────────────────────────
# COLETA COMPLETA DO SITE
# ─────────────────────────────────────────────────────────────

def coletar_todos_do_site(ids_existentes: set, forcar: bool) -> list:
    """
    Varre todas as categorias + fulltext e retorna apenas
    produtos que não existem em ids_existentes.
    """
    todos_novos = []
    ids_vistos  = set(ids_existentes)  # inclui os existentes para dedup

    print("\n📡 Etapa 1 — Varrendo categorias...")
    for cat in CATEGORIAS:
        slugs_faixas = []
        if cat["faixas"]:
            slugs_faixas = [(cat["slug"], f) for f in FAIXAS_PRECO]
            slugs_faixas.append((cat["slug"], None))  # fallback sem faixa
        else:
            slugs_faixas = [(cat["slug"], None)]

        novos_cat = 0
        bar = tqdm(desc=f"  {cat['nome']}", unit=" prod", leave=False, ncols=70)

        for slug, faixa in slugs_faixas:
            from_i = 0
            while from_i < 2490:
                prods = buscar_pagina(slug, from_i, from_i + PAGE_SIZE, faixa)
                if not prods:
                    break
                for p in prods:
                    pid = str(p.get("productId",""))
                    if pid and pid not in ids_vistos:
                        ids_vistos.add(pid)
                        todos_novos.append(extrair_produto(p, cat["nome"]))
                        novos_cat += 1
                        bar.update(1)
                if len(prods) < PAGE_SIZE + 1:
                    break
                from_i += PAGE_SIZE + 1
                time.sleep(DELAY)
            time.sleep(0.3)

        bar.close()
        status = f"✅ +{novos_cat} novos" if novos_cat else "✓ sem novidades"
        print(f"  {cat['nome']:<30} {status}")

    print("\n🔍 Etapa 2 — Busca full-text (produtos ocultos)...")
    novos_ft = 0
    bar_ft = tqdm(total=len(TERMOS_FT), desc="  Full-text", unit=" termo",
                  ncols=70, leave=False)

    for termo in TERMOS_FT:
        from_i = 0
        while from_i < 2490:
            prods = buscar_fulltext(termo, from_i, from_i + PAGE_SIZE)
            if not prods:
                break
            for p in prods:
                pid = str(p.get("productId",""))
                if pid and pid not in ids_vistos:
                    ids_vistos.add(pid)
                    # Tenta pegar categoria do path VTEX
                    cats = p.get("categories", [])
                    cat_nome = cats[0].strip("/").split("/")[-1] if cats else "Droguería"
                    todos_novos.append(extrair_produto(p, cat_nome))
                    novos_ft += 1
            if len(prods) < PAGE_SIZE + 1:
                break
            from_i += PAGE_SIZE + 1
            time.sleep(DELAY)
        bar_ft.update(1)
        time.sleep(DELAY)

    bar_ft.close()
    print(f"  Full-text: +{novos_ft} produtos adicionais encontrados")

    return todos_novos


# ─────────────────────────────────────────────────────────────
# INSERÇÃO NO BANCO
# ─────────────────────────────────────────────────────────────

def inserir_no_banco(produtos: list) -> int:
    """Insere lista de produtos no SQLite. Retorna quantos inseriu."""
    try:
        db = sqlite3.connect(DB_PATH)
        inseridos = 0
        for p in produtos:
            existe = db.execute(
                "SELECT id FROM produtos WHERE produto_id=?",
                [p["produto_id"]]).fetchone()
            if not existe:
                db.execute("""
                    INSERT INTO produtos
                    (produto_id,sku,ean,nome,marca,categoria,descricao,
                     imagem_1,imagem_2,imagem_3,imagem_4,todas_imagens,
                     preco_cop,preco_lista_cop,url_produto,ativo)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)
                """, [
                    p["produto_id"], p["sku"], p["ean"],
                    p["nome"][:500], p["marca"], p["categoria"],
                    p["descricao"], p["imagem_1"], p["imagem_2"],
                    p["imagem_3"], p["imagem_4"], p["todas_imagens"],
                    p.get("preco_cop"), p.get("preco_lista_cop"),
                    p["url_produto"],
                ])
                inseridos += 1
        db.commit()
        db.close()
        return inseridos
    except Exception as e:
        print(f"  ⚠️  Erro ao inserir no banco: {e}")
        return 0


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sincroniza produtos novos do farmaexpress.com"
    )
    parser.add_argument("--csv",    action="store_true",
                        help="Comparar com CSV em vez do banco SQLite")
    parser.add_argument("--forcar", action="store_true",
                        help="Ignorar IDs existentes e baixar tudo de novo")
    parser.add_argument("--csv-path", default="produtos_final.csv",
                        help="Caminho do CSV de referência (padrão: produtos_final.csv)")
    args = parser.parse_args()

    inicio = datetime.now()
    print()
    print("=" * 62)
    print("  farmaexpress.com — Sincronização incremental")
    print(f"  Início: {inicio.strftime('%d/%m/%Y %H:%M')}")
    print("=" * 62)

    # 1. Carregar IDs já existentes
    print("\n📂 Carregando produtos já existentes...")
    if args.forcar:
        ids_existentes = set()
        print("  ⚡ Modo forçado — baixando tudo novamente")
    elif args.csv:
        ids_existentes = ids_do_csv(args.csv_path)
    else:
        ids_existentes = ids_do_banco()
        if not ids_existentes:
            print("  ℹ️  Banco vazio ou não encontrado — tentando CSV...")
            ids_existentes = ids_do_csv(args.csv_path)

    print(f"  Total de IDs conhecidos: {len(ids_existentes)}")

    # 2. Varrer o site e coletar novos
    novos = coletar_todos_do_site(ids_existentes, args.forcar)

    # 3. Resultado
    fim = datetime.now()
    duracao = (fim - inicio).seconds // 60

    print(f"\n{'─'*62}")
    print(f"  ✅ Produtos NOVOS encontrados: {len(novos)}")
    print(f"  ⏱️  Tempo total: {duracao} minutos")
    print(f"{'─'*62}")

    if not novos:
        print("\n🎉 Catálogo já está atualizado! Nenhum produto novo.")
        return

    # 4. Salvar CSV dos novos
    df_novos = pd.DataFrame(novos)
    df_novos.to_csv(CSV_SAIDA, index=False, encoding="utf-8-sig")
    print(f"\n💾 CSV dos novos salvo: {CSV_SAIDA} ({len(novos)} produtos)")

    # 5. Inserir no banco
    print("\n📥 Inserindo no banco de dados SQLite...")
    inseridos = inserir_no_banco(novos)
    print(f"  ✅ {inseridos} produtos inseridos no banco")

    # 6. Resumo por categoria
    if not df_novos.empty:
        print("\n📊 Novos por categoria:")
        resumo = df_novos.groupby("categoria")["produto_id"].count()
        for cat, total in resumo.items():
            print(f"  {cat:<35} +{total}")

    print(f"\n🎉 Sincronização concluída! Reinicie o app.py para ver os novos produtos.")


if __name__ == "__main__":
    main()
