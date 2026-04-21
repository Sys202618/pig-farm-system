# -*- coding: utf-8 -*-
"""Initialize PostgreSQL database with all tables"""
import os
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/pigfarm')

from db_adapter import get_db_conn, USE_POSTGRES, init_postgres_tables
import hashlib

if not USE_POSTGRES:
    print("ERROR: DATABASE_URL not set. Set it to your PostgreSQL connection string.")
    print("Example: postgresql://user:pass@host:5432/dbname")
    exit(1)

conn = get_db_conn()
c = conn.cursor()

print("Creating PostgreSQL tables...")

# Users
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(64) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        token VARCHAR(64),
        token_exp TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

# Pig farms
c.execute('''
    CREATE TABLE IF NOT EXISTS pig_farms (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        address TEXT,
        manager VARCHAR(50),
        phone VARCHAR(20),
        stock_scale INTEGER,
        built_date DATE,
        area REAL,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

# Barns
c.execute('''
    CREATE TABLE IF NOT EXISTS barns (
        id SERIAL PRIMARY KEY,
        farm_id INTEGER REFERENCES pig_farms(id),
        code VARCHAR(50) NOT NULL,
        name VARCHAR(100) NOT NULL,
        barn_type VARCHAR(50),
        capacity INTEGER,
        area REAL,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(farm_id, code)
    )
''')

# Batches
c.execute('''
    CREATE TABLE IF NOT EXISTS batches (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100),
        batch_type VARCHAR(50),
        start_date DATE,
        end_date DATE,
        plan_quantity INTEGER,
        current_quantity INTEGER DEFAULT 0,
        manager VARCHAR(50),
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

# Herds
c.execute('''
    CREATE TABLE IF NOT EXISTS herds (
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        barn_id INTEGER REFERENCES barns(id),
        code VARCHAR(50) UNIQUE NOT NULL,
        pig_type VARCHAR(50),
        quantity INTEGER DEFAULT 0,
        avg_weight REAL,
        entry_date DATE,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

# Employees
c.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(50) NOT NULL,
        phone VARCHAR(20),
        id_card VARCHAR(18),
        position VARCHAR(50),
        farm_id INTEGER REFERENCES pig_farms(id),
        hire_date DATE,
        status VARCHAR(20) DEFAULT 'active',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
''')

# Production records (simplified - add more as needed)
tables = [
    ('breeding_records', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        sow_code VARCHAR(50),
        boar_code VARCHAR(50),
        breeding_date DATE,
        method VARCHAR(20),
        operator VARCHAR(50),
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('farrowing_records', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        sow_code VARCHAR(50),
        farrowing_date DATE,
        total_born INTEGER,
        live_born INTEGER,
        healthy_count INTEGER,
        weak INTEGER,
        mummy INTEGER,
        dead_born INTEGER,
        litter_weight REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('weaning_records', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        weaning_date DATE,
        piglet_count INTEGER,
        avg_weight REAL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('transfer_records', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        from_barn_id INTEGER REFERENCES barns(id),
        to_barn_id INTEGER REFERENCES barns(id),
        transfer_date DATE,
        quantity INTEGER,
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('death_records', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        death_date DATE,
        quantity INTEGER,
        reason VARCHAR(100),
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('sales_records', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        sale_date DATE,
        quantity INTEGER,
        unit_price REAL,
        total_amount REAL,
        customer VARCHAR(100),
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('income_records', '''
        id SERIAL PRIMARY KEY,
        record_date DATE,
        income_type VARCHAR(50),
        amount REAL,
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('cost_records', '''
        id SERIAL PRIMARY KEY,
        record_date DATE,
        cost_type VARCHAR(50),
        amount REAL,
        description TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('immune_plans', '''
        id SERIAL PRIMARY KEY,
        batch_id INTEGER REFERENCES batches(id),
        vaccine_name VARCHAR(100),
        planned_date DATE,
        status VARCHAR(20) DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('immune_records', '''
        id SERIAL PRIMARY KEY,
        plan_id INTEGER REFERENCES immune_plans(id),
        batch_id INTEGER REFERENCES batches(id),
        farm_id INTEGER REFERENCES pig_farms(id),
        immune_date DATE,
        operator VARCHAR(50),
        notes TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    '''),
    ('system_params', '''
        id SERIAL PRIMARY KEY,
        param_key VARCHAR(50) UNIQUE NOT NULL,
        param_value TEXT,
        updated_at TIMESTAMP DEFAULT NOW()
    '''),
]

for table_name, schema in tables:
    c.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({schema})')
    print(f"  - {table_name}")

# Insert default admin
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    pw_hash = hashlib.md5('admin123'.encode()).hexdigest()
    c.execute(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        ('admin', pw_hash, 'admin')
    )
    print("  - Created default admin user (admin/admin123)")

conn.commit()
conn.close()

print("\nPostgreSQL initialization complete!")
