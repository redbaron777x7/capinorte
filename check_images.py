import sqlite3
import urllib.request
import concurrent.futures
import sys

conn = sqlite3.connect('farmacia.db')
c = conn.cursor()

rows = c.execute("SELECT id, nome, imagem_1 FROM produtos WHERE ativo=1 AND imagem_1 IS NOT NULL AND TRIM(imagem_1)!=''").fetchall()
print(f"Total produtos com imagem: {len(rows)}")

def check_url(item):
    pid, nome, url = item
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        resp = urllib.request.urlopen(req, timeout=5)
        return (pid, nome, url, resp.status, True)
    except Exception as e:
        return (pid, nome, url, str(e), False)

sample = rows[:100]
print(f"Verificando {len(sample)} imagens (amostra)...")

broken = []
ok = 0
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(check_url, sample)
    for result in results:
        pid, nome, url, status, is_ok = result
        if is_ok:
            ok += 1
        else:
            broken.append(result)

print(f"OK: {ok}")
print(f"Quebradas: {len(broken)}")

if broken:
    print("Exemplos de imagens quebradas:")
    for pid, nome, url, status, _ in broken[:5]:
        print(f"  ID={pid}: {nome[:50]}")
        print(f"    URL: {url[:100]}")
        print(f"    Erro: {str(status)[:80]}")

broken_rate = len(broken) / len(sample) if sample else 0
print(f"Taxa de erro na amostra: {broken_rate:.1%}")

if broken_rate > 0.01:
    print("Verificando TODOS os produtos...")
    all_broken_ids = []
    batch_size = 200
    total = len(rows)
    for i in range(0, total, batch_size):
        batch = rows[i:i+batch_size]
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = list(executor.map(check_url, batch))
            for result in results:
                if not result[4]:
                    all_broken_ids.append(result[0])
        done = min(i+batch_size, total)
        print(f"  Verificados: {done}/{total} | Quebradas: {len(all_broken_ids)}")
    
    print(f"Total imagens quebradas: {len(all_broken_ids)}")
    
    with open('broken_image_ids.txt', 'w') as f:
        for pid in all_broken_ids:
            f.write(f"{pid}\n")
    print(f"IDs salvos em broken_image_ids.txt")
else:
    print("Taxa de erro baixa.")

conn.close()
