"""
批次联动迁移：为所有生产记录表添加 batch_id 外键
"""
import sqlite3
db = r'C:\Users\shiyunshu\.qclaw\workspace-agent-626766d1\pig_farm_system\data\pig_farm.db'

conn = sqlite3.connect(db)
c = conn.cursor()

tables = ['breeding_records','farrowing_records','weaning_records',
          'transfer_records','death_records','sales_records','immune_records']

for t in tables:
    c.execute(f'PRAGMA table_info({t})')
    cols = [r[1] for r in c.fetchall()]
    if 'batch_id' not in cols:
        c.execute(f'ALTER TABLE {t} ADD COLUMN batch_id INTEGER')
        print(f'Added batch_id to {t}')
    else:
        print(f'{t} already has batch_id')

conn.commit()
conn.close()
print('Done!')
