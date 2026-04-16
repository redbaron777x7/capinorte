import sqlite3

conn = sqlite3.connect('farmacia.db')
c = conn.cursor()

# Read broken image IDs
with open('broken_image_ids.txt', 'r') as f:
    broken_ids = [int(line.strip()) for line in f if line.strip()]

print(f"Total IDs com imagem quebrada: {len(broken_ids)}")

placeholder = "/static/img/no-image.png"

# Update all broken products
updated = 0
batch_size = 100
for i in range(0, len(broken_ids), batch_size):
    batch = broken_ids[i:i+batch_size]
    placeholders_sql = ','.join(['?' for _ in batch])
    c.execute(
        f"UPDATE produtos SET imagem_1=? WHERE id IN ({placeholders_sql})",
        [placeholder] + batch
    )
    updated += len(batch)

conn.commit()
print(f"Atualizados: {updated} produtos com imagem placeholder")

# Verify
remaining = c.execute(
    "SELECT COUNT(*) FROM produtos WHERE ativo=1 AND imagem_1=?", 
    [placeholder]
).fetchone()[0]
print(f"Produtos com placeholder agora: {remaining}")

conn.close()
print("Concluido!")
