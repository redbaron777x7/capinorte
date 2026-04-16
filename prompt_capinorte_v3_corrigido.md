# PROMPT COMPLETO v2 — Droguería Capinorte
# Estilo fiel a farmaexpress.com · Menu SANFONA COMPLETO · Vermelho suave · Logo Capinorte
# ========================================================================================

Crea un sitio web completo para una droguería online colombiana llamada **Capinorte Droguarías**.
Replica fielmente la estructura, secciones y experiencia del sitio **farmaexpress.com**.

El logo oficial está adjunto en la imagen (fondo rojo con ícono de curitas azul/rojo y texto
"Droguarías Capinorte" en blanco). Úsalo en el header y footer exactamente como aparece.

---

## 🎨 PALETA DE COLORES — ROJO SUAVE (no agresivo)

IMPORTANTE: El rojo debe ser cálido y profesional, NO brillante ni saturado en exceso.
El consumidor debe sentirse cómodo al ver la pantalla. Usa estos valores exactos:

```
--rojo:          #C1272D;   /* Rojo Capinorte — cálido, no eléctrico */
--rojo-hover:    #A01F24;   /* Hover y activos — más oscuro */
--rojo-oscuro:   #8B1A1E;   /* Header sticky, footer */
--rojo-suave:    #F9EAEA;   /* Fondos de secciones, badges */
--rojo-medio:    #E8C5C6;   /* Bordes, separadores */
--blanco:        #FFFFFF;
--gris-fondo:    #F5F5F5;
--gris-borde:    #E8E8E8;
--gris-texto:    #555555;
--negro:         #1A1A1A;
--wpp:           #25D366;   /* WhatsApp — nunca cambiar */
--azul-badge:    #1A4FA0;   /* Badge "Droguarías" del logo */
```

Fondo general de la página: `#F5F5F5` (no blanco puro, reduce fatiga visual)
Texto principal: `#1A1A1A` sobre fondos claros — alto contraste sin ser negro total.
Fuente: **Nunito** (Google Fonts), pesos 400 / 700 / 800 / 900.

---

## 🔝 SECCIÓN 1 — HEADER STICKY (siempre visible al hacer scroll)

### Barra mini-top (opcional, fondo --rojo-oscuro, texto blanco 11px):
```
Droguarías Capinorte · Atención Domingo a Domingo · ☎ 3022133390
```

### Header principal (fondo --rojo, height 60px desktop / 52px mobile):

Dividido en 3 zonas horizontales con flexbox:

**ZONA IZQUIERDA — Logo Capinorte:**
- Insertar la imagen adjunta del logo (fondo rojo + ícono curitas + texto Capinorte)
- Height: 44px auto-width
- Click: redirige a `/` (inicio)
- El logo ya tiene fondo rojo entonces se integra naturalmente al header
- En mobile: reducir a 36px height

**ZONA CENTRAL — Buscador (flex: 1, max-width 580px):**
- Input texto: placeholder "Busca medicamentos, marca o categoría..."
- Border-radius: 24px
- Fondo blanco, texto --negro
- Botón lupa: fondo --rojo-oscuro, ícono lupa SVG blanco, border-radius 50%
- Al escribir mínimo 2 caracteres: mostrar dropdown de autocompletado
- Dropdown: background blanco, sombra, cada ítem con imagen miniatura + nombre + precio
- En mobile: ocupa 100% del ancho disponible

**ZONA DERECHA — Botón WhatsApp:**
- Fondo #25D366, texto blanco, ícono WhatsApp SVG
- Texto: "WhatsApp"
- Border-radius: 22px
- Link: `https://wa.me/573022133390`
- En mobile: solo muestra el ícono SVG (ocultar texto con display:none)

**ZONA EXTRA (solo mobile) — Hamburger:**
- Ícono ≡ en blanco, posición izquierda del header
- Abre el DRAWER LATERAL con el menú completo

---

## 📋 SECCIÓN 2 — MENÚ ESTILO SANFONA (ACORDEÓN)
## ⚠️ ESTA SECCIÓN ES CRÍTICA — IMPLEMENTAR COMPLETA Y SEPARADA

### DESKTOP: Barra horizontal sticky (debajo del header)
- Fondo blanco, borde inferior 1px sólido --gris-borde
- Sticky: top = height del header (60px)
- Overflow-x: auto con scrollbar oculto
- Cada ítem: padding 10px 16px, font-weight 800, font-size 13px

### ÍTEMS DEL MENÚ (orden exacto — verificado en farmaexpress.com):

IMPORTANTE: La nav principal del farmaexpress.com solo tiene 3 ítems fijos.
Las 5 categorías principales aparecen como círculos en la homepage, NO en la nav.
Para Capinorte, agregamos las categorías también en la nav para mejor navegación:

```
🔥 Productos imperdibles     [color: --rojo, negrita — igual al real]
⭐ Marcas destacadas          [color: --gris-texto]
📈 Más Vendidos              [color: --gris-texto]
──── separador fino ────
💊 Medicamentos ▾            [con dropdown — subcategorías verificadas]
🧴 Cuidado Personal ▾        [con dropdown — subcategorías verificadas]
💄 Belleza ▾                 [con dropdown — subcategorías verificadas]
🏠 Mercado y Hogar ▾         [con dropdown — subcategorías verificadas]
👶 Cuidado Bebé y Mamá ▾     [con dropdown — subcategorías verificadas]
```

### DROPDOWN SANFONA — COMPORTAMIENTO EXACTO:

Cada ítem con ▾ al hacer hover (desktop) o click (mobile/tablet) abre un panel:

**Animación:** slideDown 0.25s ease, opacity 0→1
**Fondo:** blanco
**Sombra:** `0 8px 24px rgba(0,0,0,0.12)`
**Border-top:** 3px sólido --rojo
**z-index:** 500

#### DROPDOWN: 💊 Medicamentos
```
┌─────────────────────────────────────────────────┐
│  💊 MEDICAMENTOS                                │
│  ─────────────────────────────────────────────  │
│  Droguería                  Analgésicos         │
│  Antibióticos               Antiácidos          │
│  Cardiovasculares           Dermatológicos      │
│  Diabetes y Metabolismo     Homeopáticos        │
│  Complementos y Suplementos                     │
│  Productos Naturales        Fórmulas Infantiles │
└─────────────────────────────────────────────────┘
```

#### DROPDOWN: 🧴 Cuidado Personal
```
┌─────────────────────────────────────────────────┐
│  🧴 CUIDADO PERSONAL  — 3.070 productos         │
│  ─────────────────────────────────────────────  │
│  Cuidado del Cabello        Higiene Personal    │
│    ├ Shampoo                  e Íntimo          │
│    ├ Acondicionadores       Cuidado Oral        │
│    ├ Tintes para el Cabello Cuidado de la Piel  │
│    ├ Tratamientos Capilares Cuidado de los Pies │
│    └ Lacas y Geles          Salud Sexual        │
└─────────────────────────────────────────────────┘
```
Subcategorías de "Higiene Personal e Íntimo": Desodorantes y Antitranspirantes,
Protección Femenina, Jabones para el Cuerpo, Depilación y Afeitado, Antibacteriales

#### DROPDOWN: 💄 Belleza
```
┌─────────────────────────────────────────────────┐
│  💄 BELLEZA  — 1.161 productos                  │
│  ─────────────────────────────────────────────  │
│  Accesorios de belleza      Cosméticos          │
│  Dermocosmética             Limpieza facial     │
│  Perfumería y fragancias                        │
└─────────────────────────────────────────────────┘
```
⚠️ NÃO incluir "Maquillaje" — não existe como categoria no farmaexpress.com

#### DROPDOWN: 🏠 Mercado y Hogar
```
┌─────────────────────────────────────────────────┐
│  🏠 MERCADO Y HOGAR  — 785 productos            │
│  ─────────────────────────────────────────────  │
│  Confitería y Snacks        Aseo Del Hogar      │
│  Despensa                   Bebidas             │
│  Ferretería                 Tecnología          │
│  Cuidado de la Ropa                             │
└─────────────────────────────────────────────────┘
```

#### DROPDOWN: 👶 Cuidado Bebé y Mamá
```
┌─────────────────────────────────────────────────┐
│  👶 CUIDADO BEBÉ Y MAMÁ  — 596 productos        │
│  ─────────────────────────────────────────────  │
│  Accesorios Bebé            Aseo Bebé           │
│  Cuidado de la Colita       Cremas y Humectación│
│  Alimentos Infantiles       Alimentos Lácteos   │
│  Pañales                    Maternidad          │
│  Kits para Bebé             Colonias y Fragancias│
└─────────────────────────────────────────────────┘
```

### ESTILO VISUAL DOS DROPDOWNS:
- Grid de 2 colunas, gap 8px
- Cada link: padding 8px 12px, border-radius 6px
- Hover: fundo --rojo-suave, texto --rojo, font-weight 700
- Ícone ▸ antes de cada link
- Fecha ao clicar fora (click fora ou pressionar ESC)
- Em tablet: fecha automaticamente ao rolar a página

### MOBILE — DRAWER LATERAL COM SANFONA:

Drawer desliza desde a esquerda (width: 285px):

```
┌─────────────────────────────────┐
│  [LOGO CAPINORTE]          [✕] │
├─────────────────────────────────┤
│ 🏠 Inicio                       │
├─────────────────────────────────┤
│ 💊 Medicamentos             [+] │
│   ├ Droguería                   │
│   ├ Antibióticos                │
│   └ Ver más...                  │
├─────────────────────────────────┤
│ 🧴 Cuidado Personal         [+] │
│   ├ Cuidado del Cabello         │
│   └ Ver más...                  │
├─────────────────────────────────┤
│ 💄 Belleza                  [+] │
├─────────────────────────────────┤
│ 🏠 Mercado y Hogar          [+] │
├─────────────────────────────────┤
│ 👶 Cuidado Bebé y Mamá      [+] │
├─────────────────────────────────┤
│ 🔥 Productos imperdibles        │
├─────────────────────────────────┤
│ 📲 Pedir por WhatsApp           │
│    [botão verde #25D366]        │
└─────────────────────────────────┘
```

- Cada ítem com [+] ao tocar: expande subcategorias com animação slideDown
- [+] vira [–] quando aberto
- Apenas 1 ítem aberto por vez (fecha o anterior)
- Overlay escuro semitransparente ao fundo do drawer
- Click no overlay ou [✕] fecha o drawer

---

## 🖼️ SECCIÓN 3 — HERO BANNER CARRUSEL

- Carrusel automático com transição suave a cada 5 segundos
- Até **5 imagens** (gerenciadas pelo admin)
- Botões prev/next laterais semitransparentes (branco 85%)
- Dots de paginação na parte inferior
- **Swipe tátil** funcional em mobile
- Altura: 340px desktop / 200px tablet / 180px mobile
- Border-radius: 12px, margin: 14px 0
- Tamanho recomendado: **1280 × 340 px**
- Admin: subir imagem, definir link de destino, ordem, ativar/desativar

---

## 🗂️ SECCIÓN 4 — CATEGORÍAS EN CÍRCULO

**Título grande:** "Tu droguería online de confianza en medicamentos, belleza y cuidado"
**Subtítulo:** "Nuestras categorías"

Layout idêntico ao farmaexpress.com:
- Scroll horizontal (flex, overflow-x auto, sem scrollbar visível)
- 5 círculos com imagem + label embaixo

| Categoria | Ícone |
|-----------|-------|
| Medicamentos | 💊 |
| Cuidado Personal | 🧴 |
| Belleza | 💄 |
| Mercado y Hogar | 🏠 |
| Cuidado Bebé y Mamá | 👶 |

Tamanho: 80px desktop / 64px mobile
Hover: borda --rojo + scale(1.06) + sombra leve

---

## 🖼️ SECCIÓN 5 — MOSAICO "CONOCE NUESTROS DESCUENTOS"

**Título:** "Conoce nuestros descuentos"

Layout em 3 colunas, medidas EXATAS:

```
┌─────────────┬───────────────────┬─────────────┐
│  Img Esq 1  │                   │  Img Dir 1  │
│  275 × 278  │   Img Central     │  275 × 278  │
├─────────────┤   469 × 588       ├─────────────┤
│  Img Esq 2  │                   │  Img Dir 2  │
│  275 × 278  │                   │  275 × 278  │
└─────────────┴───────────────────┴─────────────┘
```

- Todas as imagens com border-radius: 10px
- Hover: scale(1.02), sombra, transition 0.2s
- Cada imagem é clicável (link configurável no admin)
- Em mobile: scroll horizontal com 5 imagens em fila
- **Admin**: seção "Mosaico Descuentos" com 5 campos de upload + link

---

## ⭐ SECCIÓN 6 — PRODUCTOS DESTACADOS

**Título:** "Productos destacados" + link "Ver más ›" à direita

- 4 produtos em scroll horizontal com flechas (← →)
- Card de produto:
  - Imagem do produto (aspect-ratio 1:1, object-fit contain)
  - Badge desconto "-15%" em --rojo
  - Marca (pequeno, cinza)
  - Nome do produto (bold)
  - Preço em --rojo, peso 900
  - Preço riscado (cinza)
  - Botão "Pedir por WhatsApp" verde
- Admin pode escolher os 4 produtos manualmente OU ativar seleção aleatória

---

## 🏷️ SECCIÓN 7 — MARCAS DESTACADAS

**Título:** "Marcas Destacadas"
**Descrição:** "Encuentra en un solo lugar las marcas más importantes y reconocidas. Contamos con productos de cuidado facial, cuidado infantil y medicamentos, tanto genéricos como de alta gama, todos disponibles en nuestro marketplace."

- Scroll horizontal de logos
- Cada logo em caixa branca, borda --gris-borde, altura 58px
- Hover: borda --rojo, sombra leve
- Logos: Bayer, Sanofi, Genfar, Novartis, Procaps, GSK, Johnson & Johnson, Pfizer

---

## 🗓️ SECCIÓN 8 — PRODUCTOS DEL MES

**Título:** "Productos del mes"
- Idêntico à seção "Productos destacados"
- Seleção independente no admin
- 4 produtos em scroll horizontal

---

## ℹ️ SECCIÓN 9 — BENEFICIOS (4 blocos com ícone)

Layout em grid 4 colunas desktop / 2×2 tablet / 1 coluna mobile.
Cada bloco: ícone em círculo --rojo-suave + título + subtítulo + texto.
Fundo branco, borda --gris-borde, border-radius 12px, padding 24px.

**Bloco 1:**
- Ícone: 🎧 (fone de ouvido)
- Título: **Atención al cliente**
- Subtítulo: *Domingo a Domingo*
- Texto: "Sabemos que tu bienestar no descansa. Por eso, en Capinorte te acompañamos todos los días, con atención al cliente de domingo a domingo, siempre listos para ayudarte."

**Bloco 2:**
- Ícone: 💰 (moneda)
- Título: **Compara precios**
- Subtítulo: *entre productos*
- Texto: "Compara precios y domicilios de droguerías cercanas en Capinorte rápida y fácilmente, asegurando siempre la mejor oferta para tus productos."

**Bloco 3:**
- Ícone: 🗂️ (catálogo)
- Título: **Amplio portafolio**
- Subtítulo: *productos para toda necesidad*
- Texto: "Bienvenido a Capinorte, tu marketplace con productos para el cuidado personal, belleza, bebé, medicamentos formulados y venta libre y más, todo de calidad y a un clic."

**Bloco 4:**
- Ícone: 🚚 (camión)
- Título: **Entrega**
- Subtítulo: *segura*
- Texto: "En Capinorte compras seguro: entregas seguras y confiables, con el respaldo de Coopidrogas y Farmacenter, líder en productos farmacéuticos de calidad en Colombia."

---

## 🦶 SECCIÓN 10 — FOOTER

Fundo --rojo-oscuro (#8B1A1E), texto branco.

### Layout 3 colunas:

**COLUNA ESQUERDA:**
- Logo Capinorte (imagem adjunta, invertida/branca se necessário)
- Ícones redes sociais (círculos brancos semi-opacos):
  - Facebook → link configurável
  - Instagram → link configurável
  - TikTok → link configurável
- Linha: © 2025 Capinorte Droguarías · Todos los derechos reservados

**COLUNA CENTRAL:**
- **Líneas de atención:** `3022133390` (tamanho grande, bold)
- Links em lista (branco, hover --rojo-suave):
  - Nosotros
  - ¿Quiénes somos?
  - Preguntas frecuentes
  - Contacto

**COLUNA DIREITA:**
- Título: "Te puede interesar"
- Links em lista:
  - Políticas y términos de uso
  - Políticas de entregas y envíos
  - Ley de protección de datos personales
  - Actividades y Promociones TyC
  - Entidades de salud

**BARRA INFERIOR DO FOOTER** (fundo ainda mais escuro):
```
Aliado: [Logo Coopidrogas]     Desarrollado con ❤️ en Colombia
```

---

## 📱 BOTÃO WHATSAPP FLUTUANTE

- `position: fixed`, `bottom: 24px`, `right: 24px`
- Círculo #25D366, diâmetro 58px desktop / 50px mobile
- Ícone WhatsApp SVG branco centralizado (24px)
- Sombra: `0 4px 20px rgba(37,211,102,0.45)`
- Animação pulse: `@keyframes pulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.08)} }` a cada 2.5s
- Hover: scale(1.12), sombra mais intensa
- Z-index: 9999
- Link: `https://wa.me/573022133390`

---

## 📲 MOBILE 100% RESPONSIVO

### Bottom Navigation Bar (só mobile, fixed no rodapé):
```
┌──────────┬──────────┬──────────┬──────────┐
│  🏠      │  📁      │  🔍      │  📲      │
│  Inicio  │Categorías│  Buscar  │WhatsApp  │
└──────────┴──────────┴──────────┴──────────┘
```
- Fundo branco, borda-top --gris-borde
- Ativo: cor --rojo
- padding-bottom: env(safe-area-inset-bottom) para iPhone

### Adaptações mobile críticas:
- Banner: 180px, swipe touch nativo
- Grid produtos: 2 colunas
- Mosaico descuentos: scroll horizontal
- Ícones categorias: 64px
- Footer: 1 coluna empilhada
- Body: padding-bottom 64px para não cobrir conteúdo com bottom nav

---

## ⚙️ ADMIN PANEL — SEÇÕES NECESSÁRIAS

| Seção Admin | O que gerencia |
|-------------|----------------|
| Carrusel Principal | Upload 5 imagens (1280×340px) + link + ordem |
| Mosaico Descuentos | 5 imagens com medidas exatas + link |
| Productos Destacados | Escolher 4 produtos ou ativar aleatório |
| Productos del Mes | Escolher 4 produtos ou ativar aleatório |
| Marcas | Adicionar/remover logos do scroll |
| Categorías | Criar, editar, reordenar, ícone emoji |
| Redes Sociales | Facebook, Instagram, TikTok (links) |
| WhatsApp | Número configurável |
| Configuración | Nome da loja, cidade, mensagem WPP |
| Dashboard | Top produtos mais clicados + gráfico 7 dias |

---

## 🔧 STACK TÉCNICO

- Backend: **Python Flask**
- Banco: **SQLite** (arquivo local `farmacia.db`)
- Templates: **Jinja2**
- Frontend: **HTML5 + CSS3 + JavaScript vanilla** (sem React/Vue)
- Fonte: **Google Fonts — Nunito** (400/700/800/900)
- Ícones: **SVG inline** (sem bibliotecas externas)
- Sem CDN de frameworks pesados

---

## ✅ CHECKLIST DE ENTREGA

### Header e Navegação:
- [ ] Header sticky fundo --rojo com logo Capinorte
- [ ] Buscador central com autocomplete dropdown
- [ ] Botão WhatsApp no header (verde)
- [ ] Botão hamburger mobile

### MENU SANFONA (PRIORIDADE MÁXIMA):
- [ ] Barra horizontal desktop com todos os 8 ítens
- [ ] Dropdown de Medicamentos com todas subcategorias
- [ ] Dropdown de Cuidado Personal com todas subcategorias
- [ ] Dropdown de Belleza com todas subcategorias
- [ ] Dropdown de Mercado y Hogar com todas subcategorias
- [ ] Dropdown de Cuidado Bebé y Mamá com todas subcategorias
- [ ] Animação slideDown suave (0.25s)
- [ ] Drawer mobile com sanfona funcional
- [ ] Cada categoria abre/fecha independentemente no mobile

### Conteúdo:
- [ ] Carrusel hero 5 imagens com swipe
- [ ] Categorias em círculo scroll horizontal
- [ ] Mosaico 5 imagens medidas exatas
- [ ] Productos Destacados (4, admin)
- [ ] Marcas scroll horizontal
- [ ] Productos del Mes (4, admin)
- [ ] 4 benefícios com ícone

### Layout e Cores:
- [ ] Vermelho suave #C1272D (não eléctrico)
- [ ] Fundo geral #F5F5F5 (não branco)
- [ ] Logo Capinorte no header e footer
- [ ] Botão WhatsApp flutuante com pulse

### Mobile:
- [ ] Bottom nav bar 4 botões
- [ ] Drawer lateral sanfona
- [ ] 100% responsivo celular/tablet/desktop

### Admin:
- [ ] Todas as 10 seções do admin funcionando
- [ ] Upload de imagens no servidor

---

*Prompt v2 — Droguarías Capinorte*
*Referência visual: farmaexpress.com*
*WhatsApp: +57 3022133390*
*Cores: Vermelho suave #C1272D · Nunito font*
