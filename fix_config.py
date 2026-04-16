import sqlite3
conn = sqlite3.connect('farmacia.db')
conn.execute("UPDATE config SET valor='573022133390' WHERE chave='whatsapp'")
conn.execute("UPDATE config SET valor='Capinorte' WHERE chave='nome_farmacia'")
conn.commit()
rows = conn.execute("SELECT chave, valor FROM config").fetchall()
for r in rows:
    print(r[0], '=', r[1])
conn.close()
print("Done!")
