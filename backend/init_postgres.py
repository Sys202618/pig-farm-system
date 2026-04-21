# -*- coding: utf-8 -*-
"""Initialize PostgreSQL database with all tables"""
import hashlib


def init_postgres_tables(conn):
    """Create all tables in PostgreSQL if they don't exist"""
    c = conn.cursor()

    tables = {
        'users': '''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(64) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                token VARCHAR(64),
                token_exp TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'pig_farms': '''
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
        ''',
        'barns': '''
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
        ''',
        'batches': '''
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
        ''',
        'herds': '''
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
        ''',
        'employees': '''
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
        ''',
        'breeding_records': '''
            CREATE TABLE IF NOT EXISTS breeding_records (
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
            )
        ''',
        'farrowing_records': '''
            CREATE TABLE IF NOT EXISTS farrowing_records (
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
            )
        ''',
        'weaning_records': '''
            CREATE TABLE IF NOT EXISTS weaning_records (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER REFERENCES batches(id),
                farm_id INTEGER REFERENCES pig_farms(id),
                weaning_date DATE,
                piglet_count INTEGER,
                avg_weight REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'transfer_records': '''
            CREATE TABLE IF NOT EXISTS transfer_records (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER REFERENCES batches(id),
                farm_id INTEGER REFERENCES pig_farms(id),
                from_barn_id INTEGER REFERENCES barns(id),
                to_barn_id INTEGER REFERENCES barns(id),
                transfer_date DATE,
                quantity INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'death_records': '''
            CREATE TABLE IF NOT EXISTS death_records (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER REFERENCES batches(id),
                farm_id INTEGER REFERENCES pig_farms(id),
                death_date DATE,
                quantity INTEGER,
                reason VARCHAR(100),
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'sales_records': '''
            CREATE TABLE IF NOT EXISTS sales_records (
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
            )
        ''',
        'income_records': '''
            CREATE TABLE IF NOT EXISTS income_records (
                id SERIAL PRIMARY KEY,
                record_date DATE,
                income_type VARCHAR(50),
                amount REAL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'cost_records': '''
            CREATE TABLE IF NOT EXISTS cost_records (
                id SERIAL PRIMARY KEY,
                record_date DATE,
                cost_type VARCHAR(50),
                amount REAL,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'immune_plans': '''
            CREATE TABLE IF NOT EXISTS immune_plans (
                id SERIAL PRIMARY KEY,
                batch_id INTEGER REFERENCES batches(id),
                vaccine_name VARCHAR(100),
                planned_date DATE,
                status VARCHAR(20) DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'immune_records': '''
            CREATE TABLE IF NOT EXISTS immune_records (
                id SERIAL PRIMARY KEY,
                plan_id INTEGER REFERENCES immune_plans(id),
                batch_id INTEGER REFERENCES batches(id),
                farm_id INTEGER REFERENCES pig_farms(id),
                immune_date DATE,
                operator VARCHAR(50),
                notes TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''',
        'system_params': '''
            CREATE TABLE IF NOT EXISTS system_params (
                id SERIAL PRIMARY KEY,
                param_key VARCHAR(50) UNIQUE NOT NULL,
                param_value TEXT,
                updated_at TIMESTAMP DEFAULT NOW()
            )
        ''',
    }

    for table_name, schema in tables.items():
        c.execute(schema)
        print(f'  [OK] {table_name}')

    # Insert default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        pw_hash = hashlib.md5('admin123'.encode()).hexdigest()
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ('admin', pw_hash, 'admin')
        )
        print('  [OK] Default admin user created (admin/admin123)')

    conn.commit()
    print('[Cloud] PostgreSQL initialization complete!')


# Allow standalone execution for manual init
if __name__ == '__main__':
    import os
    os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL') or ''
    from db_adapter import get_db_conn, USE_POSTGRES

    if not USE_POSTGRES:
        print("ERROR: Set DATABASE_URL or POSTGRES_URL environment variable first.")
        print("Example: export DATABASE_URL=postgresql://user:pass@host:5432/dbname")
        exit(1)

    conn = get_db_conn()
    init_postgres_tables(conn)
    conn.close()
