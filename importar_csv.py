"""
importar_csv.py — Importa o CSV do scraper para o banco SQLite
==============================================================
Uso: python importar_csv.py [arquivo.csv]
     Se omitido, tenta produtos_co_v3.csv, produtos_final.csv, produtos_novos.csv
"""

import sys, os, sqlite3, pandas as pd

# Garante que o script roda da pasta do projeto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = "farmacia.db"

# Escolher CSV automaticamente se não especificado
if len(sys.argv) > 1:
    CSV = sys.argv[1]
else:
    # Preferência: o mais completo disponível
    candidatos = ["produtos_co_v3.csv", "produtos_final.csv", "produtos_novos.csv",
                  "produtos_co_completo.csv", "produtos_fulltext.csv"]
    CSV = next((c for c in candidatos if os.path.exists(c)), None)
    if not CSV:
        print("❌ Nenhum CSV de produtos encontrado. Informe: python importar_csv.py <arquivo.csv>")
        sys.exit(1)

print(f"\n📂 Lendo {CSV} ...")
df = pd.read_csv(CSV, encoding="utf-8-sig", low_memory=False)
df = df.fillna("")
print(f"   {len(df)} produtos encontrados")

# Inicializar banco se não existir
db = sqlite3.connect(DB_PATH)
db.executescript("""
CREATE TABLE IF NOT EXISTS categorias (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    icone     TEXT DEFAULT '💊',
    slug      TEXT UNIQUE,
    ordem     INTEGER DEFAULT 0,
    ativo     INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS produtos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id  TEXT,
    sku         TEXT,
    ean         TEXT,
    nome        TEXT NOT NULL,
    marca       TEXT,
    categoria   TEXT,
    descricao   TEXT,
    imagem_1    TEXT,
    imagem_2    TEXT,
    imagem_3    TEXT,
    imagem_4    TEXT,
    todas_imagens TEXT,
    preco_cop   REAL,
    preco_lista_cop REAL,
    url_produto TEXT,
    ativo       INTEGER DEFAULT 1,
    destaque    INTEGER DEFAULT 0,
    produto_mes INTEGER DEFAULT 0,
    criado_em   TEXT DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS banners (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo    TEXT,
    imagem    TEXT NOT NULL,
    link      TEXT,
    tipo      TEXT DEFAULT 'principal',
    ordem     INTEGER DEFAULT 0,
    ativo     INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS mosaico (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo    TEXT,
    imagem    TEXT NOT NULL,
    link      TEXT,
    posicao   TEXT DEFAULT 'esq1',
    ativo     INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS marcas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    logo      TEXT,
    link      TEXT,
    ordem     INTEGER DEFAULT 0,
    ativo     INTEGER DEFAULT 1,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cliques (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    ip         TEXT,
    data       TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);
CREATE TABLE IF NOT EXISTS config (
    chave TEXT PRIMARY KEY,
    valor TEXT
);
INSERT OR IGNORE INTO config VALUES ('whatsapp', '573022133390');
INSERT OR IGNORE INTO config VALUES ('nome_farmacia', 'Capinorte');
INSERT OR IGNORE INTO config VALUES ('mensagem_whatsapp', 'Hola! Quiero pedir: *{produto}*. Precio: ${preco}');
INSERT OR IGNORE INTO config VALUES ('cidade', 'Colombia');
INSERT OR IGNORE INTO config VALUES ('facebook', '#');
INSERT OR IGNORE INTO config VALUES ('instagram', '#');
INSERT OR IGNORE INTO config VALUES ('tiktok', '#');
CREATE INDEX IF NOT EXISTS idx_cliques_produto ON cliques(produto_id);
CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria);
CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos(ativo);
""")
# Migração segura para coluna produto_mes
try:
    db.execute("ALTER TABLE produtos ADD COLUMN produto_mes INTEGER DEFAULT 0")
    db.commit()
except Exception:
    pass

# ─── Importar produtos ───────────────────────────────────────────────────────
inseridos = atualizados = erros = 0

def parse_preco(val):
    """Converte string de preço para float ou None."""
    try:
        v = str(val).strip().replace(",", ".")
        f = float(v)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None

print(f"   Importando para {DB_PATH} ...")

for i, (_, r) in enumerate(df.iterrows()):
    try:
        pid = str(r.get("produto_id", "")).strip()
        existe = db.execute(
            "SELECT id FROM produtos WHERE produto_id=? AND produto_id != ''",
            [pid]).fetchone() if pid else None

        campos = dict(
            produto_id      = pid,
            sku             = str(r.get("sku", "")),
            ean             = str(r.get("ean", "")),
            nome            = str(r.get("nome", ""))[:500],
            marca           = str(r.get("marca", "")),
            categoria       = str(r.get("categoria", "")),
            descricao       = str(r.get("descricao", ""))[:2000],
            imagem_1        = str(r.get("imagem_1", "")),
            imagem_2        = str(r.get("imagem_2", "")),
            imagem_3        = str(r.get("imagem_3", "")),
            imagem_4        = str(r.get("imagem_4", "")),
            todas_imagens   = str(r.get("todas_imagens", ""))[:1000],
            preco_cop       = parse_preco(r.get("preco_cop")),
            preco_lista_cop = parse_preco(r.get("preco_lista_cop")),
            url_produto     = str(r.get("url_produto", "")),
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

        # Commit em lotes de 500
        if (i + 1) % 500 == 0:
            db.commit()
            print(f"   ... {i+1} processados (inseridos={inseridos}, atualizados={atualizados})")

    except Exception as e:
        erros += 1
        if erros <= 5:
            print(f"   ⚠️  Linha {i}: {e}")

# ─── Criar categorias automaticamente ───────────────────────────────────────
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
    if cat and str(cat).strip():
        slug = (str(cat).lower()
                .replace(" ", "-").replace("é","e").replace("á","a")
                .replace("ó","o").replace("í","i").replace("ú","u").replace("ñ","n"))
        db.execute("""
            INSERT OR IGNORE INTO categorias (nome, icone, slug, ordem, ativo)
            VALUES (?,?,?,?,1)
        """, [cat, icones.get(cat, "💊"), slug, i])

db.commit()
db.close()

print(f"\n✅ Importação concluída!")
print(f"   Inseridos:   {inseridos}")
print(f"   Atualizados: {atualizados}")
print(f"   Erros:       {erros}")
print(f"   Categorias:  {len([c for c in cats if c and str(c).strip()])} criadas/verificadas")
print(f"\n▶  Agora rode: python app.py")
