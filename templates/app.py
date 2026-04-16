"""
Farmacia Online — Backend Flask
================================
Roda com: python app.py
Admin em:  http://localhost:5000/admin  (senha: admin123)
Loja em:   http://localhost:5000
"""

import os, json, sqlite3, hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template, request, jsonify,
                   redirect, url_for, session, send_from_directory,
                   abort)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "farmacia-secret-2025-mude-isso"

DB_PATH      = "farmacia.db"
UPLOAD_FOLDER = os.path.join("static", "img", "uploads")
ALLOWED_IMG   = {"png", "jpg", "jpeg", "webp", "gif"}
ADMIN_PASSWORD = "admin123"   # ← MUDE AQUI

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

# ─────────────────────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
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

    INSERT OR IGNORE INTO config VALUES ('whatsapp', '573001234567');
    INSERT OR IGNORE INTO config VALUES ('nome_farmacia', 'FarmaOnline');
    INSERT OR IGNORE INTO config VALUES ('mensagem_whatsapp', 'Hola! Quiero pedir: *{produto}*. Precio: ${preco}');
    INSERT OR IGNORE INTO config VALUES ('cidade', 'Bogotá');

    CREATE INDEX IF NOT EXISTS idx_cliques_produto ON cliques(produto_id);
    CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria);
    CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos(ativo);
    """)
    # Migrações seguras — adiciona colunas se não existirem
    for col_sql in [
        "ALTER TABLE produtos ADD COLUMN produto_mes INTEGER DEFAULT 0",
        "ALTER TABLE produtos ADD COLUMN destaque INTEGER DEFAULT 0",
    ]:
        try:
            db.execute(col_sql)
        except Exception:
            pass  # coluna já existe
    db.commit()
    db.close()

# ─────────────────────────────────────────────────────────────
# AUTENTICAÇÃO ADMIN
# ─────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    erro = None
    if request.method == "POST":
        senha = request.form.get("senha", "")
        if senha == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        erro = "Senha incorreta"
    return render_template("admin_login.html", erro=erro)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))

# ─────────────────────────────────────────────────────────────
# LOJA PÚBLICA
# ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    db = get_db()
    banners_p = db.execute(
        "SELECT * FROM banners WHERE ativo=1 AND tipo='principal' ORDER BY ordem").fetchall()
    banners_s = db.execute(
        "SELECT * FROM banners WHERE ativo=1 AND tipo='secundario' ORDER BY ordem").fetchall()
    categorias = db.execute(
        "SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    destaques = db.execute(
        "SELECT * FROM produtos WHERE ativo=1 AND destaque=1 LIMIT 12").fetchall()
    mais_clicados = db.execute("""
        SELECT p.*, COUNT(c.id) as total_cliques
        FROM produtos p
        LEFT JOIN cliques c ON p.id = c.produto_id
        WHERE p.ativo=1
        GROUP BY p.id ORDER BY total_cliques DESC LIMIT 12
    """).fetchall()
    # Produtos do Mês — seleção manual via admin (flag produto_mes=1)
    produtos_mes = db.execute(
        "SELECT * FROM produtos WHERE ativo=1 AND produto_mes=1 ORDER BY id DESC LIMIT 4"
    ).fetchall()
    # Se admin não selecionou nenhum, usa os mais clicados
    if not produtos_mes:
        produtos_mes = mais_clicados[:4]
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("store.html",
        banners_p=banners_p, banners_s=banners_s,
        categorias=categorias, destaques=destaques,
        mais_clicados=mais_clicados, produtos_mes=produtos_mes,
        config=config)

@app.route("/categoria/<nome>")
def categoria(nome):
    db = get_db()
    page  = int(request.args.get("p", 1))
    limit = 24
    offset = (page - 1) * limit
    busca = request.args.get("q", "")

    where = "WHERE p.ativo=1 AND LOWER(p.categoria)=LOWER(?)"
    params = [nome]
    if busca:
        where += " AND (LOWER(p.nome) LIKE ? OR LOWER(p.marca) LIKE ?)"
        params += [f"%{busca.lower()}%", f"%{busca.lower()}%"]

    total = db.execute(
        f"SELECT COUNT(*) FROM produtos p {where}", params).fetchone()[0]
    produtos = db.execute(
        f"SELECT * FROM produtos p {where} LIMIT ? OFFSET ?",
        params + [limit, offset]).fetchall()
    categorias = db.execute(
        "SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("categoria.html",
        produtos=produtos, categoria_atual=nome,
        categorias=categorias, config=config,
        total=total, page=page, limit=limit, busca=busca,
        pages=((total-1)//limit)+1)

@app.route("/produto/<int:pid>")
def produto(pid):
    db = get_db()
    p = db.execute("SELECT * FROM produtos WHERE id=? AND ativo=1", [pid]).fetchone()
    if not p:
        abort(404)
    # registrar clique
    db.execute("INSERT INTO cliques (produto_id, ip) VALUES (?,?)",
               [pid, request.remote_addr])
    db.commit()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    categorias = db.execute(
        "SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    relacionados = db.execute(
        "SELECT * FROM produtos WHERE categoria=? AND id!=? AND ativo=1 ORDER BY RANDOM() LIMIT 6",
        [p["categoria"], pid]).fetchall()
    db.close()
    return render_template("produto.html", p=p, config=config,
                           categorias=categorias, relacionados=relacionados)

@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").strip()
    page  = int(request.args.get("p", 1))
    limit = 24
    offset = (page - 1) * limit
    db = get_db()
    params = [f"%{q.lower()}%", f"%{q.lower()}%", f"%{q.lower()}%"]
    where = "WHERE ativo=1 AND (LOWER(nome) LIKE ? OR LOWER(marca) LIKE ? OR LOWER(descricao) LIKE ?)"
    total = db.execute(f"SELECT COUNT(*) FROM produtos {where}", params).fetchone()[0]
    produtos = db.execute(
        f"SELECT * FROM produtos {where} LIMIT ? OFFSET ?",
        params + [limit, offset]).fetchall()
    categorias = db.execute(
        "SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("buscar.html",
        produtos=produtos, q=q, total=total,
        categorias=categorias, config=config,
        page=page, limit=limit, pages=((total-1)//limit)+1 if total else 1)

# ─────────────────────────────────────────────────────────────
# ADMIN — DASHBOARD
# ─────────────────────────────────────────────────────────────

@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    total_produtos = db.execute("SELECT COUNT(*) FROM produtos WHERE ativo=1").fetchone()[0]
    total_categorias = db.execute("SELECT COUNT(*) FROM categorias WHERE ativo=1").fetchone()[0]
    total_banners = db.execute("SELECT COUNT(*) FROM banners WHERE ativo=1").fetchone()[0]
    total_cliques_hoje = db.execute(
        "SELECT COUNT(*) FROM cliques WHERE date(data)=date('now')").fetchone()[0]

    mais_clicados = db.execute("""
        SELECT p.id, p.nome, p.imagem_1, p.categoria, p.preco_cop,
               COUNT(c.id) as total_cliques
        FROM produtos p
        LEFT JOIN cliques c ON p.id = c.produto_id
        WHERE p.ativo=1
        GROUP BY p.id ORDER BY total_cliques DESC LIMIT 10
    """).fetchall()

    cliques_7d = db.execute("""
        SELECT date(data) as dia, COUNT(*) as total
        FROM cliques
        WHERE data >= date('now', '-6 days')
        GROUP BY dia ORDER BY dia
    """).fetchall()

    sem_descricao = db.execute(
        "SELECT COUNT(*) FROM produtos WHERE (descricao IS NULL OR descricao='') AND ativo=1"
    ).fetchone()[0]

    db.close()
    return render_template("admin_dashboard.html",
        total_produtos=total_produtos, total_categorias=total_categorias,
        total_banners=total_banners, total_cliques_hoje=total_cliques_hoje,
        mais_clicados=mais_clicados, cliques_7d=list(cliques_7d),
        sem_descricao=sem_descricao)

# ─────────────────────────────────────────────────────────────
# ADMIN — PRODUTOS
# ─────────────────────────────────────────────────────────────

@app.route("/admin/produtos")
@login_required
def admin_produtos():
    db = get_db()
    page  = int(request.args.get("p", 1))
    limit = 30
    offset = (page - 1) * limit
    busca = request.args.get("q", "")
    cat   = request.args.get("cat", "")

    where, params = "WHERE 1=1", []
    if busca:
        where += " AND (LOWER(nome) LIKE ? OR LOWER(marca) LIKE ?)"
        params += [f"%{busca.lower()}%", f"%{busca.lower()}%"]
    if cat:
        where += " AND categoria=?"
        params.append(cat)

    total = db.execute(f"SELECT COUNT(*) FROM produtos {where}", params).fetchone()[0]
    produtos = db.execute(
        f"SELECT * FROM produtos {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [limit, offset]).fetchall()
    categorias = db.execute("SELECT DISTINCT categoria FROM produtos WHERE categoria!='' ORDER BY categoria").fetchall()
    db.close()
    return render_template("admin_produtos.html",
        produtos=produtos, total=total, page=page, limit=limit,
        busca=busca, cat=cat, categorias=categorias,
        pages=((total-1)//limit)+1)

@app.route("/admin/produto/novo", methods=["GET","POST"])
@login_required
def admin_produto_novo():
    db = get_db()
    if request.method == "POST":
        f = request.form
        db.execute("""
            INSERT INTO produtos (nome, marca, categoria, descricao,
                imagem_1, imagem_2, imagem_3, preco_cop, preco_lista_cop,
                ativo, destaque)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, [f["nome"], f.get("marca",""), f.get("categoria",""),
              f.get("descricao",""), f.get("imagem_1",""),
              f.get("imagem_2",""), f.get("imagem_3",""),
              f.get("preco_cop") or None, f.get("preco_lista_cop") or None,
              1 if f.get("ativo") else 0,
              1 if f.get("destaque") else 0])
        db.commit()
        db.close()
        return redirect(url_for("admin_produtos"))
    categorias = db.execute("SELECT DISTINCT categoria FROM produtos WHERE categoria!='' ORDER BY categoria").fetchall()
    db.close()
    return render_template("admin_produto_form.html", p=None, categorias=categorias)

@app.route("/admin/produto/<int:pid>/editar", methods=["GET","POST"])
@login_required
def admin_produto_editar(pid):
    db = get_db()
    p = db.execute("SELECT * FROM produtos WHERE id=?", [pid]).fetchone()
    if not p:
        abort(404)
    if request.method == "POST":
        f = request.form
        db.execute("""
            UPDATE produtos SET nome=?, marca=?, categoria=?, descricao=?,
                imagem_1=?, imagem_2=?, imagem_3=?, preco_cop=?,
                preco_lista_cop=?, ativo=?, destaque=?, atualizado_em=CURRENT_TIMESTAMP
            WHERE id=?
        """, [f["nome"], f.get("marca",""), f.get("categoria",""),
              f.get("descricao",""), f.get("imagem_1",""),
              f.get("imagem_2",""), f.get("imagem_3",""),
              f.get("preco_cop") or None, f.get("preco_lista_cop") or None,
              1 if f.get("ativo") else 0,
              1 if f.get("destaque") else 0, pid])
        db.commit()
        db.close()
        return redirect(url_for("admin_produtos"))
    categorias = db.execute("SELECT DISTINCT categoria FROM produtos WHERE categoria!='' ORDER BY categoria").fetchall()
    db.close()
    return render_template("admin_produto_form.html", p=p, categorias=categorias)

@app.route("/admin/produto/<int:pid>/deletar", methods=["POST"])
@login_required
def admin_produto_deletar(pid):
    db = get_db()
    db.execute("UPDATE produtos SET ativo=0 WHERE id=?", [pid])
    db.commit()
    db.close()
    return redirect(url_for("admin_produtos"))

# ─────────────────────────────────────────────────────────────
# ADMIN — BANNERS
# ─────────────────────────────────────────────────────────────

@app.route("/admin/banners")
@login_required
def admin_banners():
    db = get_db()
    banners = db.execute("SELECT * FROM banners ORDER BY tipo, ordem").fetchall()
    db.close()
    return render_template("admin_banners.html", banners=banners)

@app.route("/admin/banner/novo", methods=["GET","POST"])
@login_required
def admin_banner_novo():
    if request.method == "POST":
        f    = request.form
        file = request.files.get("arquivo")
        imagem_url = f.get("imagem_url", "")

        if file and file.filename:
            fname = secure_filename(file.filename)
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            imagem_url = f"/static/img/uploads/{fname}"

        db = get_db()
        db.execute("""
            INSERT INTO banners (titulo, imagem, link, tipo, ordem, ativo)
            VALUES (?,?,?,?,?,?)
        """, [f.get("titulo",""), imagem_url, f.get("link",""),
              f.get("tipo","principal"), int(f.get("ordem",0)),
              1 if f.get("ativo") else 0])
        db.commit()
        db.close()
        return redirect(url_for("admin_banners"))
    return render_template("admin_banner_form.html", b=None)

@app.route("/admin/banner/<int:bid>/editar", methods=["GET","POST"])
@login_required
def admin_banner_editar(bid):
    db = get_db()
    b = db.execute("SELECT * FROM banners WHERE id=?", [bid]).fetchone()
    if not b:
        abort(404)
    if request.method == "POST":
        f    = request.form
        file = request.files.get("arquivo")
        imagem_url = f.get("imagem_url", b["imagem"])
        if file and file.filename:
            fname = secure_filename(file.filename)
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            imagem_url = f"/static/img/uploads/{fname}"
        db.execute("""
            UPDATE banners SET titulo=?, imagem=?, link=?, tipo=?, ordem=?, ativo=?
            WHERE id=?
        """, [f.get("titulo",""), imagem_url, f.get("link",""),
              f.get("tipo","principal"), int(f.get("ordem",0)),
              1 if f.get("ativo") else 0, bid])
        db.commit()
        db.close()
        return redirect(url_for("admin_banners"))
    db.close()
    return render_template("admin_banner_form.html", b=b)

@app.route("/admin/banner/<int:bid>/deletar", methods=["POST"])
@login_required
def admin_banner_deletar(bid):
    db = get_db()
    db.execute("DELETE FROM banners WHERE id=?", [bid])
    db.commit()
    db.close()
    return redirect(url_for("admin_banners"))

# ─────────────────────────────────────────────────────────────
# ADMIN — CATEGORIAS
# ─────────────────────────────────────────────────────────────

@app.route("/admin/categorias")
@login_required
def admin_categorias():
    db = get_db()
    cats = db.execute("SELECT c.*, COUNT(p.id) as total_produtos FROM categorias c LEFT JOIN produtos p ON LOWER(p.categoria)=LOWER(c.nome) AND p.ativo=1 GROUP BY c.id ORDER BY c.ordem").fetchall()
    db.close()
    return render_template("admin_categorias.html", categorias=cats)

@app.route("/admin/categorias/salvar", methods=["POST"])
@login_required
def admin_categorias_salvar():
    db = get_db()
    f  = request.form
    cid = f.get("id")
    nome = f.get("nome","").strip()
    icone = f.get("icone","💊")
    slug  = nome.lower().replace(" ", "-")
    ordem = int(f.get("ordem", 0))
    ativo = 1 if f.get("ativo") else 0

    if cid:
        db.execute("UPDATE categorias SET nome=?,icone=?,slug=?,ordem=?,ativo=? WHERE id=?",
                   [nome, icone, slug, ordem, ativo, cid])
    else:
        db.execute("INSERT INTO categorias (nome,icone,slug,ordem,ativo) VALUES (?,?,?,?,?)",
                   [nome, icone, slug, ordem, ativo])
    db.commit()
    db.close()
    return redirect(url_for("admin_categorias"))

@app.route("/admin/categorias/<int:cid>/deletar", methods=["POST"])
@login_required
def admin_categoria_deletar(cid):
    db = get_db()
    db.execute("DELETE FROM categorias WHERE id=?", [cid])
    db.commit()
    db.close()
    return redirect(url_for("admin_categorias"))

# ─────────────────────────────────────────────────────────────
# ADMIN — CONFIGURAÇÕES
# ─────────────────────────────────────────────────────────────

@app.route("/admin/config", methods=["GET","POST"])
@login_required
def admin_config():
    db = get_db()
    if request.method == "POST":
        for chave in ["whatsapp","nome_farmacia","mensagem_whatsapp","cidade"]:
            db.execute("INSERT OR REPLACE INTO config VALUES (?,?)",
                       [chave, request.form.get(chave,"")])
        db.commit()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("admin_config.html", config=config)

@app.route("/admin/descuentos", methods=["GET","POST"])
@login_required
def admin_descuentos():
    db = get_db()
    # Migração suave: adiciona coluna se não existir
    try:
        db.execute("ALTER TABLE produtos ADD COLUMN produto_mes INTEGER DEFAULT 0")
        db.commit()
    except Exception:
        pass

    if request.method == "POST":
        action = request.form.get("action")
        pid    = request.form.get("produto_id")
        if action == "add" and pid:
            # Máximo 4 produtos do mês
            count = db.execute("SELECT COUNT(*) FROM produtos WHERE produto_mes=1").fetchone()[0]
            if count < 4:
                db.execute("UPDATE produtos SET produto_mes=1 WHERE id=?", [pid])
                db.commit()
        elif action == "remove" and pid:
            db.execute("UPDATE produtos SET produto_mes=0 WHERE id=?", [pid])
            db.commit()

    produtos_mes = db.execute(
        "SELECT * FROM produtos WHERE produto_mes=1 AND ativo=1 ORDER BY id DESC"
    ).fetchall()
    # Busca para adicionar
    busca = request.args.get("q","").strip()
    resultados = []
    if busca:
        resultados = db.execute(
            "SELECT * FROM produtos WHERE ativo=1 AND produto_mes=0 "
            "AND (LOWER(nome) LIKE ? OR LOWER(marca) LIKE ?) LIMIT 10",
            [f"%{busca.lower()}%", f"%{busca.lower()}%"]).fetchall()
    db.close()
    return render_template("admin_descuentos.html",
        produtos_mes=produtos_mes, resultados=resultados, busca=busca)

# ─────────────────────────────────────────────────────────────
# API JSON (para pesquisa em tempo real)
# ─────────────────────────────────────────────────────────────

@app.route("/api/categoria")
def api_categoria():
    nome  = request.args.get("nome", "")
    limit = int(request.args.get("limit", 8))
    db    = get_db()
    rows  = db.execute(
        "SELECT id,nome,marca,imagem_1,preco_cop,preco_lista_cop,categoria "
        "FROM produtos WHERE ativo=1 AND LOWER(categoria)=LOWER(?) "
        "ORDER BY RANDOM() LIMIT ?", [nome, limit]).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/buscar")
def api_buscar():
    q = request.args.get("q","").strip().lower()
    if len(q) < 2:
        return jsonify([])
    db = get_db()
    rows = db.execute(
        "SELECT id, nome, marca, imagem_1, preco_cop, categoria FROM produtos "
        "WHERE ativo=1 AND (LOWER(nome) LIKE ? OR LOWER(marca) LIKE ?) LIMIT 8",
        [f"%{q}%", f"%{q}%"]).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    init_db()
    print("\n✅ Banco de dados inicializado")
    print("🌐 Loja:  http://localhost:5000")
    print("🔧 Admin: http://localhost:5000/admin")
    print("🔑 Senha: admin123\n")
    app.run(debug=True, port=5000)
