"""
Capinorte Droguarías — Backend Flask
=====================================
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
app.secret_key = "capinorte-secret-2025-mude-isso"

DB_PATH       = "farmacia.db"
UPLOAD_FOLDER = os.path.join("static", "img", "uploads")
ALLOWED_IMG   = {"png", "jpg", "jpeg", "webp", "gif"}
ADMIN_PASSWORD = "admin1234"   # ← MUDE AQUI

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
    # Migrate: add produto_mes column if it doesn't exist
    try:
        db.execute("ALTER TABLE produtos ADD COLUMN produto_mes INTEGER DEFAULT 0")
        db.commit()
    except Exception:
        pass
    # Migrate: audit columns for manual review
    for col_sql in [
        "ALTER TABLE produtos ADD COLUMN revisado_em TEXT",
        "ALTER TABLE produtos ADD COLUMN revisado_por TEXT DEFAULT 'admin'",
    ]:
        try:
            db.execute(col_sql)
            db.commit()
        except Exception:
            pass
    # Index for pending products query performance
    try:
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_produtos_pendente "
            "ON produtos(ativo, descricao, preco_cop)"
        )
        db.commit()
    except Exception:
        pass
    # Migrate: banner extra columns for hero redesign
    for col_sql in [
        "ALTER TABLE banners ADD COLUMN imagem_mobile TEXT",
        "ALTER TABLE banners ADD COLUMN subtitulo TEXT",
        "ALTER TABLE banners ADD COLUMN cta_texto TEXT",
        "ALTER TABLE banners ADD COLUMN cta_link TEXT",
    ]:
        try:
            db.execute(col_sql)
            db.commit()
        except Exception:
            pass
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
        erro = "Contraseña incorrecta"
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
    banners_lat_izq = db.execute(
        "SELECT * FROM banners WHERE ativo=1 AND tipo='lateral_izq' ORDER BY ordem LIMIT 1").fetchall()
    banners_promo = db.execute(
        "SELECT * FROM banners WHERE ativo=1 AND tipo='promo' ORDER BY ordem LIMIT 4").fetchall()
    categorias = db.execute(
        "SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    destaques = db.execute(
        "SELECT * FROM produtos WHERE ativo=1 AND destaque=1 ORDER BY RANDOM() LIMIT 4").fetchall()
    produtos_mes = db.execute(
        "SELECT * FROM produtos WHERE ativo=1 AND produto_mes=1 ORDER BY RANDOM() LIMIT 4").fetchall()
    # fallback aleatorio se não tiver produtos marcados
    if not destaques:
        destaques = db.execute(
            "SELECT * FROM produtos WHERE ativo=1 ORDER BY RANDOM() LIMIT 4").fetchall()
    if not produtos_mes:
        produtos_mes = db.execute(
            "SELECT * FROM produtos WHERE ativo=1 ORDER BY RANDOM() LIMIT 4").fetchall()
    marcas = db.execute(
        "SELECT * FROM marcas WHERE ativo=1 ORDER BY ordem").fetchall()
    mosaico = db.execute(
        "SELECT * FROM mosaico WHERE ativo=1 ORDER BY posicao").fetchall()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("store.html",
        banners_p=banners_p,
        banners_lat_izq=banners_lat_izq,
        banners_promo=banners_promo,
        categorias=categorias,
        destaques=destaques, produtos_mes=produtos_mes,
        marcas=marcas, mosaico=mosaico, config=config)

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
    sem_preco = db.execute(
        "SELECT COUNT(*) FROM produtos WHERE (preco_cop IS NULL OR preco_cop<=0) AND ativo=1"
    ).fetchone()[0]
    total_pendentes = db.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo=1 "
        "AND (TRIM(COALESCE(descricao,''))='' OR preco_cop IS NULL OR preco_cop<=0)"
    ).fetchone()[0]

    db.close()
    return render_template("admin_dashboard.html",
        total_produtos=total_produtos, total_categorias=total_categorias,
        total_banners=total_banners, total_cliques_hoje=total_cliques_hoje,
        mais_clicados=mais_clicados, cliques_7d=list(cliques_7d),
        sem_descricao=sem_descricao, sem_preco=sem_preco,
        total_pendentes=total_pendentes)

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
                ativo, destaque, produto_mes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, [f["nome"], f.get("marca",""), f.get("categoria",""),
              f.get("descricao",""), f.get("imagem_1",""),
              f.get("imagem_2",""), f.get("imagem_3",""),
              f.get("preco_cop") or None, f.get("preco_lista_cop") or None,
              1 if f.get("ativo") else 0,
              1 if f.get("destaque") else 0,
              1 if f.get("produto_mes") else 0])
        db.commit()
        db.close()
        return redirect(url_for("admin_produtos"))
    categorias = db.execute(
        "SELECT nome as categoria FROM categorias WHERE ativo=1 ORDER BY nome"
    ).fetchall()
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
                preco_lista_cop=?, ativo=?, destaque=?, produto_mes=?,
                atualizado_em=CURRENT_TIMESTAMP
            WHERE id=?
        """, [f["nome"], f.get("marca",""), f.get("categoria",""),
              f.get("descricao",""), f.get("imagem_1",""),
              f.get("imagem_2",""), f.get("imagem_3",""),
              f.get("preco_cop") or None, f.get("preco_lista_cop") or None,
              1 if f.get("ativo") else 0,
              1 if f.get("destaque") else 0,
              1 if f.get("produto_mes") else 0, pid])
        db.commit()
        db.close()
        return redirect(url_for("admin_produtos"))
    categorias = db.execute(
        "SELECT nome as categoria FROM categorias WHERE ativo=1 ORDER BY nome"
    ).fetchall()
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
    banners = db.execute(
        "SELECT * FROM banners ORDER BY tipo, ordem"
    ).fetchall()
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

        # Mobile image
        file_mob = request.files.get("arquivo_mobile")
        imagem_mobile_url = f.get("imagem_mobile_url", "")
        if file_mob and file_mob.filename:
            fname_m = secure_filename(file_mob.filename)
            fname_m = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_mob_{fname_m}"
            file_mob.save(os.path.join(app.config["UPLOAD_FOLDER"], fname_m))
            imagem_mobile_url = f"/static/img/uploads/{fname_m}"

        db = get_db()
        tipo_val = f.get("tipo", "principal")
        TIPOS_VALIDOS = ("principal", "lateral_izq", "lateral_der", "small_top", "small_bot", "slider", "secundario", "promo")
        if tipo_val not in TIPOS_VALIDOS:
            tipo_val = "principal"
        db.execute("""
            INSERT INTO banners (titulo, imagem, link, tipo, ordem, ativo,
                                 imagem_mobile, subtitulo, cta_texto, cta_link)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, [f.get("titulo",""), imagem_url, f.get("link",""),
              tipo_val, int(f.get("ordem",0)),
              1 if f.get("ativo") else 0,
              imagem_mobile_url, f.get("subtitulo",""),
              f.get("cta_texto",""), f.get("cta_link","")])
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

        # Mobile image
        file_mob = request.files.get("arquivo_mobile")
        imagem_mobile_url = f.get("imagem_mobile_url", b["imagem_mobile"] or "")
        if file_mob and file_mob.filename:
            fname_m = secure_filename(file_mob.filename)
            fname_m = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_mob_{fname_m}"
            file_mob.save(os.path.join(app.config["UPLOAD_FOLDER"], fname_m))
            imagem_mobile_url = f"/static/img/uploads/{fname_m}"

        tipo_val = f.get("tipo", "principal")
        TIPOS_VALIDOS = ("principal", "lateral_izq", "lateral_der", "small_top", "small_bot", "slider", "secundario", "promo")
        if tipo_val not in TIPOS_VALIDOS:
            tipo_val = "principal"
        db.execute("""
            UPDATE banners SET titulo=?, imagem=?, link=?, tipo=?, ordem=?, ativo=?,
                               imagem_mobile=?, subtitulo=?, cta_texto=?, cta_link=?
            WHERE id=?
        """, [f.get("titulo",""), imagem_url, f.get("link",""),
              tipo_val, int(f.get("ordem",0)),
              1 if f.get("ativo") else 0,
              imagem_mobile_url, f.get("subtitulo",""),
              f.get("cta_texto",""), f.get("cta_link",""), bid])
        db.commit()
        db.close()
        return redirect(url_for("admin_banners"))
    db.close()
    return render_template("admin_banner_form.html", b=b)

@app.route("/admin/banner/<int:bid>/deletar", methods=["GET","POST"])
@login_required
def admin_banner_deletar(bid):
    db = get_db()
    # Buscar imagens antes de deletar para remover os arquivos
    banner = db.execute("SELECT imagem, imagem_mobile FROM banners WHERE id=?", [bid]).fetchone()
    if banner:
        for img_field in ['imagem', 'imagem_mobile']:
            img_path = banner[img_field] if banner[img_field] else ''
            if img_path and img_path.startswith('/static/img/uploads/'):
                file_path = os.path.normpath(os.path.join(os.path.dirname(__file__), img_path.lstrip('/')))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass
    db.execute("DELETE FROM banners WHERE id=?", [bid])
    db.commit()
    db.close()
    return redirect(url_for("admin_banners"))

# ─────────────────────────────────────────────────────────────
# ADMIN — MOSAICO DESCUENTOS
# ─────────────────────────────────────────────────────────────

MOSAICO_POSICOES = [
    ("esq1", "Izquierda arriba — 275×278px"),
    ("esq2", "Izquierda abajo — 275×278px"),
    ("centro", "Centro — 469×588px"),
    ("dir1", "Derecha arriba — 275×278px"),
    ("dir2", "Derecha abajo — 275×278px"),
]

@app.route("/admin/mosaico")
@login_required
def admin_mosaico():
    db = get_db()
    items = db.execute("SELECT * FROM mosaico ORDER BY posicao").fetchall()
    db.close()
    return render_template("admin_mosaico.html", items=items,
                           posicoes=MOSAICO_POSICOES)

@app.route("/admin/mosaico/novo", methods=["GET","POST"])
@login_required
def admin_mosaico_novo():
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
            INSERT INTO mosaico (titulo, imagem, link, posicao, ativo)
            VALUES (?,?,?,?,?)
        """, [f.get("titulo",""), imagem_url, f.get("link",""),
              f.get("posicao","centro"), 1 if f.get("ativo") else 0])
        db.commit()
        db.close()
        return redirect(url_for("admin_mosaico"))
    return render_template("admin_mosaico_form.html", item=None,
                           posicoes=MOSAICO_POSICOES)

@app.route("/admin/mosaico/<int:mid>/editar", methods=["GET","POST"])
@login_required
def admin_mosaico_editar(mid):
    db = get_db()
    item = db.execute("SELECT * FROM mosaico WHERE id=?", [mid]).fetchone()
    if not item:
        abort(404)
    if request.method == "POST":
        f    = request.form
        file = request.files.get("arquivo")
        imagem_url = f.get("imagem_url", item["imagem"])
        if file and file.filename:
            fname = secure_filename(file.filename)
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            imagem_url = f"/static/img/uploads/{fname}"
        db.execute("""
            UPDATE mosaico SET titulo=?, imagem=?, link=?, posicao=?, ativo=?
            WHERE id=?
        """, [f.get("titulo",""), imagem_url, f.get("link",""),
              f.get("posicao","centro"), 1 if f.get("ativo") else 0, mid])
        db.commit()
        db.close()
        return redirect(url_for("admin_mosaico"))
    db.close()
    return render_template("admin_mosaico_form.html", item=item,
                           posicoes=MOSAICO_POSICOES)

@app.route("/admin/mosaico/<int:mid>/deletar", methods=["POST"])
@login_required
def admin_mosaico_deletar(mid):
    db = get_db()
    db.execute("DELETE FROM mosaico WHERE id=?", [mid])
    db.commit()
    db.close()
    return redirect(url_for("admin_mosaico"))

# ─────────────────────────────────────────────────────────────
# ADMIN — MARCAS
# ─────────────────────────────────────────────────────────────

@app.route("/admin/marcas")
@login_required
def admin_marcas():
    db = get_db()
    marcas = db.execute("SELECT * FROM marcas ORDER BY ordem").fetchall()
    db.close()
    return render_template("admin_marcas.html", marcas=marcas)

@app.route("/admin/marca/novo", methods=["GET","POST"])
@login_required
def admin_marca_novo():
    if request.method == "POST":
        f    = request.form
        file = request.files.get("arquivo")
        logo_url = f.get("logo_url", "")
        if file and file.filename:
            fname = secure_filename(file.filename)
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            logo_url = f"/static/img/uploads/{fname}"
        db = get_db()
        db.execute("""
            INSERT INTO marcas (nome, logo, link, ordem, ativo)
            VALUES (?,?,?,?,?)
        """, [f.get("nome",""), logo_url, f.get("link",""),
              int(f.get("ordem",0)), 1 if f.get("ativo") else 0])
        db.commit()
        db.close()
        return redirect(url_for("admin_marcas"))
    return render_template("admin_marca_form.html", m=None)

@app.route("/admin/marca/<int:mid>/editar", methods=["GET","POST"])
@login_required
def admin_marca_editar(mid):
    db = get_db()
    m = db.execute("SELECT * FROM marcas WHERE id=?", [mid]).fetchone()
    if not m:
        abort(404)
    if request.method == "POST":
        f    = request.form
        file = request.files.get("arquivo")
        logo_url = f.get("logo_url", m["logo"])
        if file and file.filename:
            fname = secure_filename(file.filename)
            fname = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{fname}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            logo_url = f"/static/img/uploads/{fname}"
        db.execute("""
            UPDATE marcas SET nome=?, logo=?, link=?, ordem=?, ativo=?
            WHERE id=?
        """, [f.get("nome",""), logo_url, f.get("link",""),
              int(f.get("ordem",0)), 1 if f.get("ativo") else 0, mid])
        db.commit()
        db.close()
        return redirect(url_for("admin_marcas"))
    db.close()
    return render_template("admin_marca_form.html", m=m)

@app.route("/admin/marca/<int:mid>/deletar", methods=["POST"])
@login_required
def admin_marca_deletar(mid):
    db = get_db()
    db.execute("DELETE FROM marcas WHERE id=?", [mid])
    db.commit()
    db.close()
    return redirect(url_for("admin_marcas"))

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
    cid  = f.get("id")
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
        for chave in ["whatsapp","nome_farmacia","mensagem_whatsapp",
                      "cidade","facebook","instagram","tiktok"]:
            db.execute("INSERT OR REPLACE INTO config VALUES (?,?)",
                       [chave, request.form.get(chave,"")])
        db.commit()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("admin_config.html", config=config)

@app.route("/admin/config/senha", methods=["POST"])
@login_required
def admin_config_senha():
    global ADMIN_PASSWORD
    senha_atual = request.form.get("senha_atual", "")
    senha_nova  = request.form.get("senha_nova", "")
    senha_conf  = request.form.get("senha_conf", "")

    db = get_db()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())

    # Validações
    if senha_atual != ADMIN_PASSWORD:
        db.close()
        return render_template("admin_config.html", config=config,
                               msg_senha="❌ Contraseña actual incorrecta.", msg_senha_ok=False)

    if len(senha_nova) < 6:
        db.close()
        return render_template("admin_config.html", config=config,
                               msg_senha="❌ La nueva contraseña debe tener mínimo 6 caracteres.", msg_senha_ok=False)

    if senha_nova != senha_conf:
        db.close()
        return render_template("admin_config.html", config=config,
                               msg_senha="❌ Las contraseñas no coinciden.", msg_senha_ok=False)

    # Atualizar a senha
    ADMIN_PASSWORD = senha_nova
    db.close()
    return render_template("admin_config.html", config=config,
                           msg_senha="✅ Contraseña cambiada exitosamente.", msg_senha_ok=True)

# ─────────────────────────────────────────────────────────────
# ADMIN — PRODUTOS DO MÊS
# ─────────────────────────────────────────────────────────────

@app.route("/admin/descuentos", methods=["GET","POST"])
@login_required
def admin_descuentos():
    db = get_db()

    if request.method == "POST":
        action     = request.form.get("action")
        produto_id = request.form.get("produto_id")
        if action == "add":
            # só adiciona se ainda há menos de 4
            count = db.execute(
                "SELECT COUNT(*) FROM produtos WHERE produto_mes=1 AND ativo=1"
            ).fetchone()[0]
            if count < 4:
                db.execute(
                    "UPDATE produtos SET produto_mes=1 WHERE id=?", [produto_id]
                )
                db.commit()
        elif action == "remove":
            db.execute(
                "UPDATE produtos SET produto_mes=0 WHERE id=?", [produto_id]
            )
            db.commit()
        db.close()
        # preserva a busca ao redirecionar
        q = request.form.get("q", "")
        return redirect(url_for("admin_descuentos") + (f"?q={q}" if q else ""))

    # GET — lista actuais e resultados de busca
    busca = request.args.get("q", "").strip()
    produtos_mes = db.execute(
        "SELECT * FROM produtos WHERE produto_mes=1 AND ativo=1 ORDER BY nome"
    ).fetchall()

    resultados = []
    if busca:
        ids_mes = [str(p["id"]) for p in produtos_mes]
        placeholders = ",".join(ids_mes) if ids_mes else "0"
        resultados = db.execute(
            f"""SELECT * FROM produtos
                WHERE ativo=1
                  AND id NOT IN ({placeholders})
                  AND (LOWER(nome) LIKE ? OR LOWER(marca) LIKE ?)
                ORDER BY nome LIMIT 30""",
            [f"%{busca.lower()}%", f"%{busca.lower()}%"]
        ).fetchall()

    db.close()
    return render_template("admin_descuentos.html",
                           produtos_mes=produtos_mes,
                           resultados=resultados,
                           busca=busca)

# ─────────────────────────────────────────────────────────────
# PÁGINAS LEGAIS
# ─────────────────────────────────────────────────────────────

@app.route("/terminos")
def terminos():
    db = get_db()
    categorias = db.execute("SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("terminos.html", categorias=categorias, config=config)

@app.route("/privacidad")
def privacidad():
    db = get_db()
    categorias = db.execute("SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("privacidad.html", categorias=categorias, config=config)

@app.route("/envios")
def envios():
    db = get_db()
    categorias = db.execute("SELECT * FROM categorias WHERE ativo=1 ORDER BY ordem").fetchall()
    config = dict(db.execute("SELECT chave, valor FROM config").fetchall())
    db.close()
    return render_template("envios.html", categorias=categorias, config=config)

# ─────────────────────────────────────────────────────────────
# ADMIN — PRODUCTOS PENDIENTES
# ─────────────────────────────────────────────────────────────

PENDIENTES_SQL = """
    WHERE ativo=1
      AND (
        TRIM(COALESCE(descricao,'')) = ''
        OR preco_cop IS NULL
        OR preco_cop <= 0
      )
"""

@app.route("/admin/pendentes")
@login_required
def admin_pendentes():
    db = get_db()
    page  = int(request.args.get("p", 1))
    limit = 30
    offset = (page - 1) * limit
    busca = request.args.get("q", "").strip()
    filtro = request.args.get("filtro", "todos")  # todos | sem_desc | sem_precio

    where = "WHERE ativo=1 AND (TRIM(COALESCE(descricao,''))='' OR preco_cop IS NULL OR preco_cop<=0)"
    params = []

    if filtro == "sem_desc":
        where = "WHERE ativo=1 AND TRIM(COALESCE(descricao,''))=''"
    elif filtro == "sem_precio":
        where = "WHERE ativo=1 AND (preco_cop IS NULL OR preco_cop<=0)"

    if busca:
        where += " AND (LOWER(nome) LIKE ? OR LOWER(marca) LIKE ? OR LOWER(sku) LIKE ?)"
        params += [f"%{busca.lower()}%", f"%{busca.lower()}%", f"%{busca.lower()}%"]

    total = db.execute(f"SELECT COUNT(*) FROM produtos {where}", params).fetchone()[0]
    produtos = db.execute(
        f"SELECT * FROM produtos {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()

    total_geral = db.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo=1 "
        "AND (TRIM(COALESCE(descricao,''))='' OR preco_cop IS NULL OR preco_cop<=0)"
    ).fetchone()[0]

    db.close()
    return render_template("admin_pendentes.html",
        produtos=produtos, total=total, page=page, limit=limit,
        busca=busca, filtro=filtro, total_geral=total_geral,
        pages=((total-1)//limit)+1 if total else 1)


@app.route("/admin/pendentes/<int:pid>/salvar", methods=["POST"])
@login_required
def admin_pendentes_salvar(pid):
    """API endpoint para salvar descripción e precio via AJAX."""
    import logging
    data = request.get_json(silent=True) or {}

    descricao = data.get("descricao", "").strip()
    preco_raw = data.get("preco_cop", "")

    # Validações
    erros = []
    if not descricao:
        erros.append("La descripción es obligatoria.")

    preco_cop = None
    if preco_raw != "" and preco_raw is not None:
        try:
            preco_cop = float(str(preco_raw).replace(",", ".").replace(" ", ""))
            if preco_cop < 0:
                erros.append("El precio no puede ser negativo.")
        except (ValueError, TypeError):
            erros.append("Precio inválido. Use solo números.")

    if erros:
        return jsonify({"ok": False, "erros": erros}), 400

    db = get_db()
    p = db.execute("SELECT id FROM produtos WHERE id=? AND ativo=1", [pid]).fetchone()
    if not p:
        db.close()
        return jsonify({"ok": False, "erros": ["Producto no encontrado."]}), 404

    db.execute(
        """
        UPDATE produtos
        SET descricao=?, preco_cop=?,
            revisado_em=CURRENT_TIMESTAMP,
            revisado_por='admin',
            atualizado_em=CURRENT_TIMESTAMP
        WHERE id=?
        """,
        [descricao, preco_cop, pid]
    )
    db.commit()

    # Verifica se ainda fica pendente após salvar
    ainda_pendente = db.execute(
        "SELECT 1 FROM produtos WHERE id=? AND "
        "(TRIM(COALESCE(descricao,''))='' OR preco_cop IS NULL OR preco_cop<=0)",
        [pid]
    ).fetchone()

    db.close()
    logging.info(f"[PENDENTES] Produto #{pid} atualizado. Ainda pendente: {bool(ainda_pendente)}")

    return jsonify({
        "ok": True,
        "ainda_pendente": bool(ainda_pendente),
        "msg": "Guardado con éxito."
    })


@app.route("/api/admin/pendentes/count")
@login_required
def api_pendentes_count():
    """Retorna contagem de produtos pendentes para badge no menu."""
    db = get_db()
    count = db.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo=1 "
        "AND (TRIM(COALESCE(descricao,''))='' OR preco_cop IS NULL OR preco_cop<=0)"
    ).fetchone()[0]
    db.close()
    return jsonify({"count": count})


@app.route("/admin/tools/limpar-precos", methods=["POST"])
@login_required
def admin_limpar_precos():
    """Zera o preço de todos os produtos ativos — ação irreversível."""
    import logging
    db = get_db()
    total = db.execute(
        "SELECT COUNT(*) FROM produtos WHERE ativo=1 AND preco_cop IS NOT NULL"
    ).fetchone()[0]
    db.execute(
        "UPDATE produtos SET preco_cop=NULL, preco_lista_cop=NULL, "
        "atualizado_em=CURRENT_TIMESTAMP WHERE ativo=1"
    )
    db.commit()
    db.close()
    logging.warning(f"[TOOLS] Preços zerados: {total} produtos afetados.")
    return jsonify({"ok": True, "total": total,
                    "msg": f"Precios eliminados: {total} productos actualizados."})


# ─────────────────────────────────────────────────────────────
# API JSON
# ─────────────────────────────────────────────────────────────

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
    print("\n[OK] Banco de dados inicializado")
    print("[LOJA]  http://localhost:5000")
    print("[ADMIN] http://localhost:5000/admin")
    print("[SENHA] admin123\n")
    app.run(debug=True, port=5000)
