"""
Farmaexpress — Verificador de Imagens
======================================
Lê o CSV gerado e verifica TODAS as imagens via HEAD request
(sem baixar) para calcular o espaço total necessário.

Requisitos:
  pip install requests pandas tqdm

Uso:
  python verificar_imagens.py
"""

import requests
import pandas as pd
from tqdm import tqdm
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

CSV_INPUT   = "produtos_co_v3.csv"
RELATORIO   = "relatorio_imagens.txt"
JSON_OUT    = "imagens_detalhes.json"

TIMEOUT     = 10
MAX_WORKERS = 20      # requisições paralelas (HEAD é leve)
DELAY       = 0.0     # HEAD requests são rápidos, sem delay

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}

# ─────────────────────────────────────────────────────────
def checar_imagem(url: str) -> dict:
    """Faz HEAD request e retorna tamanho e tipo da imagem."""
    resultado = {
        "url":          url,
        "status":       None,
        "tamanho_kb":   None,
        "tipo":         None,
        "ok":           False,
        "erro":         None,
    }
    if not url or not url.startswith("http"):
        resultado["erro"] = "URL vazia"
        return resultado

    try:
        r = requests.head(url, headers=HEADERS, timeout=TIMEOUT,
                          allow_redirects=True)
        resultado["status"] = r.status_code
        resultado["ok"]     = r.status_code == 200

        tamanho = r.headers.get("Content-Length")
        if tamanho:
            resultado["tamanho_kb"] = round(int(tamanho) / 1024, 1)

        tipo = r.headers.get("Content-Type", "")
        resultado["tipo"] = tipo.split(";")[0].strip()

    except requests.Timeout:
        resultado["erro"] = "Timeout"
    except requests.ConnectionError:
        resultado["erro"] = "Conexão recusada"
    except Exception as e:
        resultado["erro"] = str(e)

    return resultado


def formatar_tamanho(total_kb: float) -> str:
    if total_kb < 1024:
        return f"{total_kb:.0f} KB"
    elif total_kb < 1024 * 1024:
        return f"{total_kb/1024:.1f} MB"
    else:
        return f"{total_kb/1024/1024:.2f} GB"


# ─────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 60)
    print("  Farmaexpress — Verificador de Imagens")
    print("=" * 60)

    # 1. Carregar CSV
    print(f"\n📂 Lendo {CSV_INPUT} ...")
    df = pd.read_csv(CSV_INPUT, encoding="utf-8-sig", low_memory=False)
    print(f"   {len(df)} produtos carregados")

    # 2. Coletar todas as URLs únicas de imagem
    colunas_img = ["imagem_1", "imagem_2", "imagem_3", "imagem_4"]
    todas_urls = set()

    for col in colunas_img:
        if col in df.columns:
            urls = df[col].dropna().astype(str)
            urls = urls[urls.str.startswith("http")]
            todas_urls.update(urls.tolist())

    # Também pega URLs extras do campo todas_imagens
    if "todas_imagens" in df.columns:
        for cell in df["todas_imagens"].dropna():
            for url in str(cell).split(" | "):
                url = url.strip()
                if url.startswith("http"):
                    todas_urls.add(url)

    todas_urls = sorted(todas_urls)
    print(f"   {len(todas_urls)} URLs de imagem únicas encontradas\n")

    # 3. Verificar tamanho de cada imagem em paralelo
    print(f"🔍 Verificando imagens (HEAD requests, {MAX_WORKERS} paralelos) ...")
    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(checar_imagem, url): url
                   for url in todas_urls}

        barra = tqdm(total=len(futures), unit=" img", ncols=70)
        for future in as_completed(futures):
            res = future.result()
            resultados.append(res)
            barra.update(1)
        barra.close()

    # 4. Análise dos resultados
    ok          = [r for r in resultados if r["ok"]]
    com_tamanho = [r for r in ok if r["tamanho_kb"] is not None]
    sem_tamanho = [r for r in ok if r["tamanho_kb"] is None]
    erros       = [r for r in resultados if not r["ok"]]

    total_kb_real = sum(r["tamanho_kb"] for r in com_tamanho)

    # Estimar tamanho das sem Content-Length (usa média das que têm)
    media_kb = (total_kb_real / len(com_tamanho)) if com_tamanho else 150
    estimativa_sem = len(sem_tamanho) * media_kb
    total_estimado_kb = total_kb_real + estimativa_sem

    # Por tipo de arquivo
    tipos = defaultdict(int)
    for r in ok:
        tipos[r.get("tipo") or "desconhecido"] += 1

    # Por faixa de tamanho
    faixas = {"< 50 KB": 0, "50–100 KB": 0, "100–300 KB": 0,
              "300–500 KB": 0, "> 500 KB": 0}
    for r in com_tamanho:
        kb = r["tamanho_kb"]
        if kb < 50:
            faixas["< 50 KB"] += 1
        elif kb < 100:
            faixas["50–100 KB"] += 1
        elif kb < 300:
            faixas["100–300 KB"] += 1
        elif kb < 500:
            faixas["300–500 KB"] += 1
        else:
            faixas["> 500 KB"] += 1

    # 5. Relatório
    linhas = []
    linhas.append("=" * 60)
    linhas.append("  RELATÓRIO DE IMAGENS — Farmaexpress.com")
    linhas.append("=" * 60)
    linhas.append("")
    linhas.append(f"  Total de URLs únicas verificadas : {len(todas_urls):>8}")
    linhas.append(f"  Imagens OK (acessíveis)          : {len(ok):>8}")
    linhas.append(f"    ↳ com Content-Length            : {len(com_tamanho):>8}")
    linhas.append(f"    ↳ sem Content-Length (estimado) : {len(sem_tamanho):>8}")
    linhas.append(f"  Imagens com erro / inacessíveis  : {len(erros):>8}")
    linhas.append("")
    linhas.append("─" * 60)
    linhas.append("  ESPAÇO NECESSÁRIO PARA ARMAZENAR")
    linhas.append("─" * 60)
    linhas.append(f"  Tamanho medido (Content-Length)  : {formatar_tamanho(total_kb_real):>10}")
    linhas.append(f"  Estimativa total (todas)         : {formatar_tamanho(total_estimado_kb):>10}")
    linhas.append(f"  Média por imagem                 : {formatar_tamanho(media_kb):>10}")
    linhas.append("")
    linhas.append("─" * 60)
    linhas.append("  PROJEÇÃO POR RESOLUÇÃO")
    linhas.append("─" * 60)
    n = len(todas_urls)
    linhas.append(f"  Original CDN (atual)             : {formatar_tamanho(total_estimado_kb):>10}")
    linhas.append(f"  Thumb 300×300 (~20 KB cada)      : {formatar_tamanho(n*20):>10}")
    linhas.append(f"  Médio 600×600 (~60 KB cada)      : {formatar_tamanho(n*60):>10}")
    linhas.append(f"  Alta 1200×1200 (~200 KB cada)    : {formatar_tamanho(n*200):>10}")
    linhas.append("")
    linhas.append("─" * 60)
    linhas.append("  DISTRIBUIÇÃO POR FAIXA DE TAMANHO")
    linhas.append("─" * 60)
    for faixa, cnt in faixas.items():
        pct = cnt / len(com_tamanho) * 100 if com_tamanho else 0
        barra_visual = "█" * int(pct / 3)
        linhas.append(f"  {faixa:<15} {cnt:>5} imgs  {pct:>5.1f}%  {barra_visual}")
    linhas.append("")
    linhas.append("─" * 60)
    linhas.append("  TIPOS DE ARQUIVO")
    linhas.append("─" * 60)
    for tipo, cnt in sorted(tipos.items(), key=lambda x: -x[1]):
        linhas.append(f"  {tipo:<30} {cnt:>6} imgs")
    linhas.append("")

    if erros:
        linhas.append("─" * 60)
        linhas.append(f"  ERROS ({len(erros)} imagens inacessíveis)")
        linhas.append("─" * 60)
        tipos_erro = defaultdict(int)
        for e in erros:
            tipos_erro[e.get("erro") or f"HTTP {e.get('status')}"] += 1
        for err, cnt in sorted(tipos_erro.items(), key=lambda x: -x[1]):
            linhas.append(f"  {err:<40} {cnt:>5}")
        linhas.append("")

    linhas.append("=" * 60)
    relatorio_str = "\n".join(linhas)

    print()
    print(relatorio_str)

    # Salvar relatório TXT
    with open(RELATORIO, "w", encoding="utf-8") as f:
        f.write(relatorio_str)
    print(f"\n✅ Relatório salvo: {RELATORIO}")

    # Salvar JSON com detalhes de cada imagem
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print(f"✅ Detalhes JSON:   {JSON_OUT}")
    print("\n🎉 Verificação concluída!")


if __name__ == "__main__":
    main()
