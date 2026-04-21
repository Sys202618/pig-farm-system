"""个体猪只管理迁移：herds表添加 ear_tag + gender 字段"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pig_farm.db')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 添加 ear_tag 字段
try:
    c.execute("ALTER TABLE herds ADD COLUMN ear_tag TEXT")
    print("Added ear_tag")
except Exception as e:
    print(f"ear_tag: {e}")

# 添加 gender 字段
try:
    c.execute("ALTER TABLE herds ADD COLUMN gender TEXT DEFAULT '公'")
    print("Added gender")
except Exception as e:
    print(f"gender: {e}")

# 为已有数据生成 ear_tag（如果 herd_code 存在就复用）
c.execute("SELECT id, herd_code FROM herds WHERE ear_tag IS NULL OR ear_tag = ''")
rows = c.fetchall()
for row in rows:
    ear_tag = row['herd_code'] or f"P{str(row['id']).zfill(4)}"
    c.execute("UPDATE herds SET ear_tag = ? WHERE id = ?", (ear_tag, row['id']))
print(f"Updated {len(rows)} existing records with ear_tag")

# 设置 ear_tag 为 UNIQUE（SQLite 不支持 ALTER ADD CONSTRAINT，通过索引实现）
try:
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_herds_ear_tag ON herds(ear_tag)")
    print("Created unique index on ear_tag")
except Exception as e:
    print(f"unique index: {e}")

conn.commit()
conn.close()
print("Migration complete!")
