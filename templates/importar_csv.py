"""
importar_csv.py — Importa o CSV do scraper para o banco SQLite
==============================================================
Uso: python importar_csv.py produtos_co_v3.csv
"""

import sys, sqlite3, pandas as pd
from app import init_db, DB_PATH

CSV = sys.argv[1] if len(sys.argv) > 1 else "produtos_co_v3.csv"

print(f"\n📂 Lendo {CSV} ...")
df = pd.read_csv(CSV, encoding="utf-8-sig", low_memory=False)
df = df.fillna("")
print(f"   {len(df)} produtos encontrados")

init_db()
db = sqlite3.connect(DB_PATH)

# Importar produtos
inseridos = atualizados = 0
for _, r in df.iterrows():
    existe = db.execute(
        "SELECT id FROM produtos WHERE produto_id=?",
        [str(r.get("produto_id",""))]).fetchone()

    campos = dict(
        produto_id      = str(r.get("produto_id","")),
        sku             = str(r.get("sku","")),
        ean             = str(r.get("ean","")),
        nome            = str(r.get("nome",""))[:500],
        marca           = str(r.get("marca","")),
        categoria       = str(r.get("categoria","")),
        descricao       = str(r.get("descricao","")),
        imagem_1        = str(r.get("imagem_1","")),
        imagem_2        = str(r.get("imagem_2","")),
        imagem_3        = str(r.get("imagem_3","")),
        imagem_4        = str(r.get("imagem_4","")),
        todas_imagens   = str(r.get("todas_imagens","")),
        preco_cop       = float(r["preco_cop"]) if str(r.get("preco_cop","")).replace(".","").isdigit() else None,
        preco_lista_cop = float(r["preco_lista_cop"]) if str(r.get("preco_lista_cop","")).replace(".","").isdigit() else None,
        url_produto     = str(r.get("url_produto","")),
    )

    if existe:
        db.execute("""
            UPDATE produtos SET sku=:sku, ean=:ean, nome=:nome, marca=:marca,
                categoria=:categoria, descricao=:descricao,
                imagem_1=:imagem_1, imagem_2=:imagem_2, imagem_3=:imagem_3,
                imagem_4=:imagem_4, todas_imagens=:todas_imagens,
                preco_cop=:preco_cop, preco_lista_cop=:preco_lista_cop,
                url_produto=:url_produto, atualizado_em=CURRENT_TIMESTAMP
            WHERE produto_id=:produto_id
        """, campos)
        atualizados += 1
    else:
        db.execute("""
            INSERT INTO produtos (produto_id,sku,ean,nome,marca,categoria,descricao,
                imagem_1,imagem_2,imagem_3,imagem_4,todas_imagens,
                preco_cop,preco_lista_cop,url_produto)
            VALUES (:produto_id,:sku,:ean,:nome,:marca,:categoria,:descricao,
                :imagem_1,:imagem_2,:imagem_3,:imagem_4,:todas_imagens,
                :preco_cop,:preco_lista_cop,:url_produto)
        """, campos)
        inseridos += 1

# Criar categorias automaticamente a partir das categorias dos produtos
cats = df["categoria"].dropna().unique()
icones = {
    "Droguería":                 "💊",
    "Cuidado Personal":          "🧴",
    "Belleza":                   "💄",
    "Mercado y Hogar":           "🏠",
    "Cuidado Bebé y Mamá":       "👶",
    "Complementos y Suplementos":"💪",
    "Productos Naturales":       "🌿",
    "Fórmulas Infantiles":       "🍼",
    "Homeopáticos":              "🌸",
}
for i, cat in enumerate(sorted(cats)):
    if cat:
        slug = cat.lower().replace(" ", "-").replace("é","e").replace("á","a")
        db.execute("""
            INSERT OR IGNORE INTO categorias (nome, icone, slug, ordem, ativo)
            VALUES (?,?,?,?,1)
        """, [cat, icones.get(cat, "💊"), slug, i])

db.commit()
db.close()

print(f"\n✅ Importação concluída!")
print(f"   Inseridos:   {inseridos}")
print(f"   Atualizados: {atualizados}")
print(f"   Categorias:  {len(cats)} criadas automaticamente")
print(f"\n▶  Agora rode: python app.py")
