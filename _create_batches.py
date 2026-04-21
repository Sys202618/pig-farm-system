"""
批次管理数据库改造
1. 创建 batches 表
2. 给 herds 添加 batch_id 外键（强制非空）
"""
import sqlite3, os

DB_PATH = r'C:\Users\shiyunshu\.qclaw\workspace-agent-626766d1\pig_farm_system\data\pig_farm.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. 创建 batches 表
c.execute('''
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_code TEXT NOT NULL UNIQUE,
    batch_name TEXT,
    farm_id INTEGER NOT NULL,
    batch_type TEXT NOT NULL,
    start_date DATE NOT NULL,
    expected_end_date DATE,
    quantity INTEGER DEFAULT 0,
    status TEXT DEFAULT '进行中',
    manager TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 2. 检查 herds 表是否已有 batch_id
c.execute('PRAGMA table_info(herds)')
herd_cols = [r[1] for r in c.fetchall()]
print('Current herds columns:', herd_cols)

if 'batch_id' not in herd_cols:
    # 备份 herds 数据
    c.execute('SELECT * FROM herds')
    herd_rows = c.fetchall()
    print(f'Herds rows: {len(herd_rows)}')
    
    # 重建 herds 表（batch_id 必填）
    c.execute('DROP TABLE herds')
    c.execute('''
    CREATE TABLE herds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farm_id INTEGER,
        barn_id INTEGER,
        batch_id INTEGER NOT NULL,
        herd_code TEXT,
        herd_name TEXT,
        pig_type TEXT,
        quantity INTEGER DEFAULT 0,
        weight REAL DEFAULT 0,
        age_days INTEGER DEFAULT 0,
        in_date DATE,
        transfer_date DATE,
        status TEXT DEFAULT '存栏',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 迁移旧数据（给个临时批次ID=1）
    # 先插入一个默认批次
    c.execute('''
    INSERT OR IGNORE INTO batches (id, batch_code, batch_name, farm_id, batch_type, start_date, status)
    VALUES (1, 'LEGACY001', '历史批次', 1, '育肥批次', '2026-01-01', '已完成')
    ''')
    
    # 迁移旧 herds 数据（batch_id 设为1）
    for row in herd_rows:
        # 旧表结构: id, farm_id, barn_id, batch_no, pig_type, quantity, in_date, status, notes, created_at, herd_code, herd_name, age_days, transfer_date, weight
        if len(row) >= 15:
            c.execute('''
            INSERT INTO herds (id, farm_id, barn_id, batch_id, herd_code, herd_name, pig_type, quantity, weight, age_days, in_date, transfer_date, status, notes, created_at)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (row[0], row[1], row[2], row[10], row[11], row[4], row[5], row[14], row[12], row[6], row[13], row[7], row[9], row[8]))
    
    print('Herds migrated with batch_id=1 (legacy batch)')

conn.commit()

# 验证
c.execute('PRAGMA table_info(batches)')
print('Batches schema:', [(r[1], r[2], r[3]) for r in c.fetchall()])
c.execute('PRAGMA table_info(herds)')
print('Herds schema:', [(r[1], r[2], r[3]) for r in c.fetchall()])

conn.close()
print('Done!')