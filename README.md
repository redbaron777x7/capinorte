# 💊 FarmaOnline — Site de Farmácia

Site completo de farmácia com painel admin, integração WhatsApp e importação do CSV do scraper.

---

## 📁 Estrutura do projeto

```
farmacia/
├── app.py                  ← Servidor Flask (backend)
├── importar_csv.py         ← Importa o CSV do scraper
├── requirements.txt        ← Dependências Python
├── farmacia.db             ← Banco de dados (criado automaticamente)
├── static/
│   └── img/
│       ├── no-img.png      ← Imagem padrão sem foto
│       └── uploads/        ← Banners enviados pelo admin
└── templates/              ← Páginas HTML
```

---

## ⚡ Instalação rápida (Windows)

### 1. Instalar dependências
```powershell
pip install flask flask-cors pandas pillow werkzeug
```

### 2. Copie o CSV do scraper para esta pasta
```
produtos_co_v3.csv  →  coloque na pasta farmacia/
```

### 3. Importar os produtos
```powershell
python importar_csv.py produtos_co_v3.csv
```

### 4. Rodar o servidor
```powershell
python app.py
```

### 5. Acessar
- 🌐 **Loja:**  http://localhost:5000
- 🔧 **Admin:** http://localhost:5000/admin
- 🔑 **Senha:**  `admin123`

---

## 🔧 Painel Admin — Funcionalidades

| Função | Onde |
|--------|------|
| Ver produtos mais clicados | Dashboard |
| Gráfico de cliques 7 dias | Dashboard |
| Adicionar produto manualmente | Produtos → Novo |
| Editar nome/descrição/preço | Produtos → ✏️ |
| Marcar produto como destaque | Produtos → ✏️ → ☑ Destacado |
| Adicionar banner principal | Banners → Novo → Tipo: Principal |
| Adicionar banner secundário | Banners → Novo → Tipo: Secundario |
| Criar nova categoria | Categorias → Formulário |
| Alterar número WhatsApp | Configuración |
| Alterar nome da farmácia | Configuración |

---

## 📐 Tamanhos de banners

| Tipo | Tamanho | Uso |
|------|---------|-----|
| Principal | **1280 × 340 px** | Slider grande do topo |
| Secundário | **600 × 140 px** | Mini banners abaixo do slider |

---

## 📲 Como funciona o WhatsApp

Quando o cliente clica em **"Pedir por WhatsApp"**, o site abre o WhatsApp com:
```
Hola! Quiero pedir: *Nome do Produto*. Precio: $15.000
```

Configure o número em **Admin → Configuración → Número WhatsApp**.
Formato: `573001234567` (código país 57 + número sem espaços)

---

## 🚀 Colocar online (deploy)

### Opção 1 — PythonAnywhere (grátis)
1. Crie conta em pythonanywhere.com
2. Upload dos arquivos
3. Configure o WSGI apontando para `app.py`

### Opção 2 — Railway / Render (grátis)
1. Suba o projeto no GitHub
2. Conecte no Railway.app ou Render.com
3. Deploy automático

### Opção 3 — VPS (DigitalOcean, Hostinger)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:80 app:app
```

---

## 🔑 Mudar senha do admin

No arquivo `app.py`, linha:
```python
ADMIN_PASSWORD = "admin123"   # ← mude aqui
```

---

## 📦 Atualizar o catálogo (re-scraping)

```powershell
# Rodar o scraper novamente
python farmaexpress_v3.py

# Importar atualizações (não duplica, só atualiza)
python importar_csv.py produtos_co_v3.csv
```

---

**Desenvolvido com Flask + SQLite + Jinja2**
