import sqlite3
db = sqlite3.connect('farmacia.db')
db.row_factory = sqlite3.Row
cats = db.execute('SELECT categoria, COUNT(*) as n FROM produtos WHERE ativo=1 GROUP BY categoria ORDER BY n DESC LIMIT 15').fetchall()
for r in cats:
    print(f'{str(r["categoria"]):40} {r["n"]}')
print()
total = db.execute('SELECT COUNT(*) FROM produtos WHERE ativo=1').fetchone()[0]
print(f'TOTAL ATIVOS: {total}')
db.close()
