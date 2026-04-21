# -*- coding: utf-8 -*-
"""猪场生产+财务管理系统 - 数据库模型与初始化"""
import sqlite3
import os
import hashlib
from datetime import datetime


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_tables()
        self._migrate_tables()

    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_tables(self):
        conn = self.get_conn()
        c = conn.cursor()

        # 用户表
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'production',
            name TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 猪场（扩展字段）
        c.execute('''CREATE TABLE IF NOT EXISTS pig_farms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            address TEXT,
            manager TEXT,
            phone TEXT,
            stock_scale INTEGER DEFAULT 0,
            built_date DATE,
            area REAL DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT '正常',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 猪舍（扩展字段）
        c.execute('''CREATE TABLE IF NOT EXISTS barns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            barn_code TEXT,
            name TEXT NOT NULL,
            barn_type TEXT NOT NULL,
            area REAL DEFAULT 0,
            capacity INTEGER DEFAULT 0,
            current_count INTEGER DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT '正常',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 员工（扩展字段）
        c.execute('''CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            role TEXT,
            dept TEXT,
            phone TEXT,
            status TEXT DEFAULT '在职',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 猪群/批次（扩展字段）
        c.execute('''CREATE TABLE IF NOT EXISTS herds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            barn_id INTEGER,
            herd_code TEXT,
            herd_name TEXT,
            batch_no TEXT NOT NULL,
            pig_type TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            in_date DATE,
            age_days INTEGER DEFAULT 0,
            transfer_date DATE,
            status TEXT DEFAULT '在群',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id),
            FOREIGN KEY (barn_id) REFERENCES barns(id)
        )''')

        # 配种记录
        c.execute('''CREATE TABLE IF NOT EXISTS breeding_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            sow_code TEXT NOT NULL,
            boar_code TEXT,
            breed_date DATE NOT NULL,
            breed_method TEXT,
            operator TEXT,
            expected_date DATE,
            status TEXT DEFAULT '已配种',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 产仔记录
        c.execute('''CREATE TABLE IF NOT EXISTS farrowing_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            batch_id INTEGER,
            sow_code TEXT NOT NULL,
            farrow_date DATE NOT NULL,
            total_born INTEGER DEFAULT 0,
            alive_born INTEGER DEFAULT 0,
            healthy_count INTEGER DEFAULT 0,
            dead_born INTEGER DEFAULT 0,
            mummy INTEGER DEFAULT 0,
            weak INTEGER DEFAULT 0,
            avg_weight REAL DEFAULT 0,
            litter_weight REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 断奶记录
        c.execute('''CREATE TABLE IF NOT EXISTS weaning_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            sow_code TEXT,
            wean_date DATE NOT NULL,
            weaned_count INTEGER DEFAULT 0,
            avg_weight REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 转舍记录
        c.execute('''CREATE TABLE IF NOT EXISTS transfer_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            pig_type TEXT,
            from_barn TEXT,
            to_barn TEXT,
            quantity INTEGER DEFAULT 0,
            transfer_date DATE NOT NULL,
            operator TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 死亡/淘汰记录
        c.execute('''CREATE TABLE IF NOT EXISTS death_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            pig_type TEXT,
            barn_name TEXT,
            quantity INTEGER DEFAULT 0,
            death_type TEXT DEFAULT '死亡',
            reason TEXT,
            death_date DATE NOT NULL,
            operator TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 销售记录
        c.execute('''CREATE TABLE IF NOT EXISTS sales_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            pig_type TEXT NOT NULL,
            quantity INTEGER DEFAULT 0,
            total_weight REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            buyer TEXT,
            sale_date DATE NOT NULL,
            operator TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 收入记录
        c.execute('''CREATE TABLE IF NOT EXISTS income_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            income_type TEXT NOT NULL,
            amount REAL DEFAULT 0,
            month TEXT NOT NULL,
            description TEXT,
            record_date DATE NOT NULL,
            operator TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 成本记录
        c.execute('''CREATE TABLE IF NOT EXISTS cost_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            cost_category TEXT NOT NULL,
            amount REAL DEFAULT 0,
            month TEXT NOT NULL,
            description TEXT,
            record_date DATE NOT NULL,
            operator TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 系统参数表
        c.execute('''CREATE TABLE IF NOT EXISTS system_params (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            param_key TEXT NOT NULL UNIQUE,
            param_name TEXT NOT NULL,
            param_value TEXT,
            param_type TEXT DEFAULT 'text',
            options TEXT,
            category TEXT DEFAULT 'general',
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # 免疫计划表
        c.execute('''CREATE TABLE IF NOT EXISTS immune_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER,
            vaccine_name TEXT NOT NULL,
            immune_type TEXT,
            immune_age INTEGER DEFAULT 0,
            immune_method TEXT,
            dosage TEXT,
            interval_days INTEGER DEFAULT 0,
            notes TEXT,
            status TEXT DEFAULT '启用',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id)
        )''')

        # 免疫记录表
        c.execute('''CREATE TABLE IF NOT EXISTS immune_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER NOT NULL,
            herd_id INTEGER,
            herd_code TEXT,
            herd_name TEXT,
            barn_id INTEGER,
            barn_name TEXT,
            batch_no TEXT,
            pig_type TEXT,
            immune_date DATE NOT NULL,
            vaccine_name TEXT NOT NULL,
            immune_type TEXT,
            immune_age INTEGER,
            quantity INTEGER DEFAULT 0,
            immune_method TEXT,
            dosage TEXT,
            operator TEXT,
            adverse_reaction TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES pig_farms(id),
            FOREIGN KEY (herd_id) REFERENCES herds(id)
        )''')

        # 创建默认管理员
        c.execute('SELECT COUNT(*) FROM users')
        if c.fetchone()[0] == 0:
            pwd = hashlib.md5('admin123'.encode()).hexdigest()
            c.execute('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)',
                      ('admin', pwd, 'admin', '系统管理员'))
            c.execute('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)',
                      ('production', pwd, 'production', '生产员'))
            c.execute('INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)',
                      ('finance', pwd, 'finance', '财务员'))

        # 初始化默认系统参数
        c.execute('SELECT COUNT(*) FROM system_params')
        if c.fetchone()[0] == 0:
            default_params = [
                ('unit_weight', '体重默认单位', 'kg', 'select', 'kg,斤', 'general', '体重计量单位'),
                ('unit_money', '金额默认单位', '元', 'select', '元,万元', 'general', '金额计量单位'),
                ('pig_spec', '商品规格', '100-120kg', 'text', '', 'general', '出栏商品猪规格'),
                ('immune_reminder_days', '免疫提醒天数', '7', 'number', '', 'production', '免疫到期前N天提醒'),
                ('weaning_days', '断奶天数', '21', 'number', '', 'production', '标准断奶日龄'),
                ('sale_days', '出栏天数', '180', 'number', '', 'production', '标准出栏日龄'),
                ('nursery_days', '保育天数', '49', 'number', '', 'production', '保育阶段天数'),
                ('gestation_days', '妊娠天数', '114', 'number', '', 'production', '妊娠天数'),
                ('inventory_warning', '存栏预警上限(%)', '95', 'number', '', 'production', '超过容量N%预警'),
                ('price_piglet', '仔猪单价默认值', '500', 'number', '', 'finance', '仔猪默认单价(元/头)'),
                ('price_fattening', '育肥猪单价默认值', '16', 'number', '', 'finance', '育肥猪默认单价(元/kg)'),
                ('price_semen', '猪精单价默认值', '20', 'number', '', 'finance', '猪精默认单价(元/份)'),
                ('barn_capacity_warning', '舍内上限(%)', '90', 'number', '', 'production', '猪舍存栏上限'),
            ]
            for p in default_params:
                c.execute('INSERT INTO system_params (param_key, param_name, param_value, param_type, options, category, description) VALUES (?, ?, ?, ?, ?, ?, ?)', p)

        # 初始化默认免疫计划
        c.execute('SELECT COUNT(*) FROM immune_plans')
        if c.fetchone()[0] == 0:
            default_plans = [
                ('猪瘟疫苗', '基础免疫', 0, '肌注', '1头份/头', 21, '首免'),
                ('猪瘟疫苗', '基础免疫', 21, '肌注', '1头份/头', 0, '二免'),
                ('蓝耳疫苗', '基础免疫', 14, '肌注', '1头份/头', 0, '经产母猪'),
                ('圆环疫苗', '基础免疫', 14, '肌注', '1头份/头', 0, '仔猪'),
                ('伪狂犬疫苗', '基础免疫', 0, '滴鼻', '1头份/头', 42, '首免'),
                ('伪狂犬疫苗', '基础免疫', 42, '肌注', '1头份/头', 0, '二免'),
                ('口蹄疫疫苗', '基础免疫', 56, '肌注', '2ml/头', 90, '育肥猪'),
                ('细小病毒疫苗', '基础免疫', 0, '肌注', '1头份/头', 0, '后备母猪'),
                ('乙脑疫苗', '基础免疫', 0, '肌注', '1头份/头', 180, '种猪'),
                ('驱虫', '驱虫', 42, '口服', '按体重', 0, '保育猪驱虫'),
                ('驱虫', '驱虫', 0, '口服', '按体重', 90, '育肥猪驱虫'),
            ]
            for p in default_plans:
                c.execute('INSERT INTO immune_plans (vaccine_name, immune_type, immune_age, immune_method, dosage, interval_days, notes) VALUES (?, ?, ?, ?, ?, ?, ?)', p)

        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")

    def _migrate_tables(self):
        """增量迁移：为已有表添加新增字段"""
        conn = self.get_conn()
        c = conn.cursor()
        
        migrations = {
            'pig_farms': ['stock_scale', 'built_date', 'area', 'notes'],
            'barns': ['barn_code', 'area', 'notes'],
            'employees': ['dept'],
            'herds': ['herd_code', 'herd_name', 'age_days', 'transfer_date'],
            'immune_records': ['adverse_reaction'],
            'farrowing_records': ['batch_id', 'healthy_count', 'litter_weight'],
        }
        
        for table, new_cols in migrations.items():
            for col in new_cols:
                try:
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT")
                except:
                    pass
        
        conn.commit()
        conn.close()


# 全局数据库实例
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        from config import Config
        _db_instance = Database(Config.DATABASE_PATH)
    return _db_instance
