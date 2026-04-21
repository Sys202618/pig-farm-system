# -*- coding: utf-8 -*-
"""
猪场数据管理与成本核算系统 - 数据库模型
"""
import sqlite3
import os
from datetime import datetime


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """初始化所有数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ========== 1. 组织架构表 ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS region (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region_code TEXT UNIQUE NOT NULL,
                region_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_code TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                region_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (region_code) REFERENCES region(region_code)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farm_line (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_code TEXT UNIQUE NOT NULL,
                line_name TEXT NOT NULL,
                company_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_code) REFERENCES company(company_code)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pig_farm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT UNIQUE NOT NULL,
                farm_name TEXT NOT NULL,
                farm_line TEXT,
                region TEXT,
                company TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS department (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_code TEXT UNIQUE NOT NULL,
                dept_name TEXT NOT NULL,
                farm_code TEXT,
                stage TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (farm_code) REFERENCES pig_farm(farm_code)
            )
        ''')
        
        # ========== 2. 基础信息表 ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pig_house (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                house_code TEXT UNIQUE NOT NULL,
                house_name TEXT NOT NULL,
                farm_code TEXT,
                stage TEXT,
                capacity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pig_group (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_code TEXT UNIQUE NOT NULL,
                group_name TEXT NOT NULL,
                stage TEXT,
                farm_code TEXT,
                batch_no TEXT,
                entry_date TEXT,
                head_count INTEGER,
                avg_weight REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pig_batch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_no TEXT UNIQUE NOT NULL,
                stage TEXT,
                farm_code TEXT,
                breeding_date TEXT,
                expected_farrow_date TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_code TEXT UNIQUE NOT NULL,
                staff_name TEXT NOT NULL,
                dept_code TEXT,
                position TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS material (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_code TEXT UNIQUE NOT NULL,
                material_name TEXT NOT NULL,
                unit TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== 3. 生产数据表 ==========
        
        # 3.1 配种记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breeding_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                breeding_date TEXT,
                sow_no TEXT,
                boar_no TEXT,
                staff_code TEXT,
                breeding_type TEXT,
                heat_interval INTEGER,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.2 分娩记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS farrow_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                farrow_date TEXT,
                sow_no TEXT,
                total_born INTEGER,
                healthy_piglets INTEGER,
                weak_piglets INTEGER,
                dead_piglets INTEGER,
                mummy INTEGER,
                staff_code TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.3 断奶记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weaning_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                weaning_date TEXT,
                sow_no TEXT,
                piglet_count INTEGER,
                piglet_weight REAL,
                avg_weight REAL,
                staff_code TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.4 转群记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfer_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                transfer_date TEXT,
                pig_no TEXT,
                from_stage TEXT,
                to_stage TEXT,
                head_count INTEGER,
                total_weight REAL,
                avg_weight REAL,
                transfer_type TEXT,
                staff_code TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.5 销售记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                sales_date TEXT,
                pig_no TEXT,
                pig_type TEXT,
                sales_type TEXT,
                head_count INTEGER,
                total_weight REAL,
                avg_weight REAL,
                unit_price REAL,
                total_amount REAL,
                staff_code TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.6 死亡记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS death_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                death_date TEXT,
                pig_no TEXT,
                stage TEXT,
                head_count INTEGER,
                weight REAL,
                death_reason TEXT,
                staff_code TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.7 淘汰记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cull_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                cull_date TEXT,
                pig_no TEXT,
                stage TEXT,
                head_count INTEGER,
                weight REAL,
                cull_reason TEXT,
                staff_code TEXT,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3.8 库存记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                stage TEXT,
                head_count INTEGER,
                total_weight REAL,
                avg_weight REAL,
                avg_age INTEGER,
                feed_consumption REAL,
                feed_weight REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== 4. 成本数据表 ==========
        
        # 4.1 平行结转表（成本核心数据）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parallel_transfer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                stage TEXT NOT NULL,
                subject_code TEXT NOT NULL,
                subject_name TEXT,
                amount REAL DEFAULT 0,
                weight REAL DEFAULT 0,
                head_count INTEGER DEFAULT 0,
                feed_weight REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_code, period, stage, subject_code)
            )
        ''')
        
        # 4.2 繁殖汇总表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breeding_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                breeding_count INTEGER DEFAULT 0,
                return_heat_count INTEGER DEFAULT 0,
                empty_check_count INTEGER DEFAULT 0,
                abortion_count INTEGER DEFAULT 0,
                farrow_count INTEGER DEFAULT 0,
                pregnant_sales INTEGER DEFAULT 0,
                total_born INTEGER DEFAULT 0,
                healthy_piglets INTEGER DEFAULT 0,
                weak_piglets INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_code, period)
            )
        ''')
        
        # 4.3 变动汇总表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                stage TEXT NOT NULL,
                opening_head INTEGER DEFAULT 0,
                opening_weight REAL DEFAULT 0,
                entry_head INTEGER DEFAULT 0,
                entry_weight REAL DEFAULT 0,
                transfer_in_head INTEGER DEFAULT 0,
                transfer_in_weight REAL DEFAULT 0,
                transfer_out_head INTEGER DEFAULT 0,
                transfer_out_weight REAL DEFAULT 0,
                sales_head INTEGER DEFAULT 0,
                sales_weight REAL DEFAULT 0,
                death_head INTEGER DEFAULT 0,
                death_weight REAL DEFAULT 0,
                cull_head INTEGER DEFAULT 0,
                cull_weight REAL DEFAULT 0,
                closing_head INTEGER DEFAULT 0,
                closing_weight REAL DEFAULT 0,
                total_feed REAL DEFAULT 0,
                total_feed_weight REAL DEFAULT 0,
                daily_gain REAL DEFAULT 0,
                feed_conversion_rate REAL DEFAULT 0,
                mortality_rate REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_code, period, stage)
            )
        ''')
        
        # 4.4 仔猪转出表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS piglet_transfer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                transfer_type TEXT NOT NULL,
                head_count INTEGER DEFAULT 0,
                total_weight REAL DEFAULT 0,
                avg_weight REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                total_cost REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_code, period, transfer_type)
            )
        ''')
        
        # 4.5 精液生产表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semen_production (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                avg_stock REAL DEFAULT 0,
                total_semen INTEGER DEFAULT 0,
                internal_use INTEGER DEFAULT 0,
                external_sales INTEGER DEFAULT 0,
                production_cost REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_code, period)
            )
        ''')
        
        # 4.6 种猪存栏表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breeding_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                stage TEXT NOT NULL,
                head_count INTEGER DEFAULT 0,
                head_days INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_code, period, stage)
            )
        ''')
        
        # 4.7 猪只变动明细表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pig_movement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                stage TEXT NOT NULL,
                movement_type TEXT NOT NULL,
                head_count INTEGER DEFAULT 0,
                weight REAL DEFAULT 0,
                cost REAL DEFAULT 0,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4.8 精液接收表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semen_receiving (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_code TEXT NOT NULL,
                period TEXT NOT NULL,
                receiving_date TEXT,
                semen_no TEXT,
                boar_no TEXT,
                quantity INTEGER,
                staff_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== 5. 用户与权限表 ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                farm_codes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== 6. 操作日志表 ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                operation_type TEXT,
                table_name TEXT,
                record_id INTEGER,
                old_value TEXT,
                new_value TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== 7. 数据校验规则表 ==========
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validation_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_code TEXT UNIQUE NOT NULL,
                rule_name TEXT,
                rule_type TEXT,
                min_value REAL,
                max_value REAL,
                warning_value REAL,
                critical_value REAL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        self._create_indexes(cursor)
        
        conn.commit()
        conn.close()
        print(f"数据库初始化完成: {self.db_path}")
    
    def _create_indexes(self, cursor):
        """创建数据库索引"""
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_parallel_farm_period ON parallel_transfer(farm_code, period)',
            'CREATE INDEX IF NOT EXISTS idx_parallel_stage ON parallel_transfer(stage)',
            'CREATE INDEX IF NOT EXISTS idx_breeding_farm_period ON breeding_summary(farm_code, period)',
            'CREATE INDEX IF NOT EXISTS idx_change_farm_period ON change_summary(farm_code, period, stage)',
            'CREATE INDEX IF NOT EXISTS idx_sales_farm_period ON sales_record(farm_code, period)',
            'CREATE INDEX IF NOT EXISTS idx_transfer_farm_period ON transfer_record(farm_code, period)',
            'CREATE INDEX IF NOT EXISTS idx_death_farm_period ON death_record(farm_code, period)',
            'CREATE INDEX IF NOT EXISTS idx_farrow_farm_period ON farrow_record(farm_code, period)',
            'CREATE INDEX IF NOT EXISTS idx_weaning_farm_period ON weaning_record(farm_code, period)',
        ]
        for idx in indexes:
            cursor.execute(idx)
    
    def query(self, sql, params=None):
        """执行查询"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        result = cursor.fetchall()
        conn.close()
        return result
    
    def execute(self, sql, params=None):
        """执行更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        lastrowid = cursor.lastrowid
        conn.close()
        return lastrowid
    
    def executemany(self, sql, params_list):
        """批量执行"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        conn.commit()
        conn.close()
    
    def get_farms(self, farm_codes=None):
        """获取场次列表"""
        if farm_codes:
            placeholders = ','.join(['?' for _ in farm_codes])
            sql = f"SELECT * FROM pig_farm WHERE farm_code IN ({placeholders})"
            return self.query(sql, farm_codes)
        return self.query("SELECT * FROM pig_farm")
    
    def get_farm_by_code(self, farm_code):
        """根据编码获取场次"""
        result = self.query("SELECT * FROM pig_farm WHERE farm_code = ?", (farm_code,))
        return result[0] if result else None
    
    def get_cost_data(self, farm_code, period, stage=None):
        """获取成本数据"""
        if stage:
            sql = "SELECT * FROM parallel_transfer WHERE farm_code = ? AND period = ? AND stage = ?"
            return self.query(sql, (farm_code, period, stage))
        else:
            sql = "SELECT * FROM parallel_transfer WHERE farm_code = ? AND period = ?"
            return self.query(sql, (farm_code, period))
    
    def save_cost_data(self, data):
        """保存成本数据"""
        sql = '''
            INSERT OR REPLACE INTO parallel_transfer 
            (farm_code, period, stage, subject_code, subject_name, amount, weight, head_count, feed_weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.executemany(sql, data)
    
    def get_breeding_summary(self, farm_code, period):
        """获取繁殖汇总"""
        result = self.query(
            "SELECT * FROM breeding_summary WHERE farm_code = ? AND period = ?",
            (farm_code, period)
        )
        return dict(result[0]) if result else None
    
    def save_breeding_summary(self, data):
        """保存繁殖汇总"""
        sql = '''
            INSERT OR REPLACE INTO breeding_summary 
            (farm_code, period, breeding_count, return_heat_count, empty_check_count,
             abortion_count, farrow_count, pregnant_sales, total_born, healthy_piglets, weak_piglets)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.executemany(sql, data)
    
    def get_change_summary(self, farm_code, period, stage=None):
        """获取变动汇总"""
        if stage:
            result = self.query(
                "SELECT * FROM change_summary WHERE farm_code = ? AND period = ? AND stage = ?",
                (farm_code, period, stage)
            )
        else:
            result = self.query(
                "SELECT * FROM change_summary WHERE farm_code = ? AND period = ?",
                (farm_code, period)
            )
        return [dict(r) for r in result]
    
    def save_change_summary(self, data):
        """保存变动汇总"""
        sql = '''
            INSERT OR REPLACE INTO change_summary 
            (farm_code, period, stage, opening_head, opening_weight, entry_head, entry_weight,
             transfer_in_head, transfer_in_weight, transfer_out_head, transfer_out_weight,
             sales_head, sales_weight, death_head, death_weight, cull_head, cull_weight,
             closing_head, closing_weight, total_feed, total_feed_weight, daily_gain,
             feed_conversion_rate, mortality_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.executemany(sql, data)
    
    def get_sales_data(self, farm_code, period):
        """获取销售数据"""
        return self.query(
            "SELECT * FROM sales_record WHERE farm_code = ? AND period = ?",
            (farm_code, period)
        )
    
    def save_sales_data(self, data):
        """保存销售数据"""
        sql = '''
            INSERT OR REPLACE INTO sales_record 
            (farm_code, period, sales_date, pig_no, pig_type, sales_type, head_count,
             total_weight, avg_weight, unit_price, total_amount, staff_code, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.executemany(sql, data)
    
    def get_production_records(self, table_name, farm_code, period):
        """获取生产记录"""
        valid_tables = ['breeding_record', 'farrow_record', 'weaning_record', 
                        'transfer_record', 'death_record', 'cull_record']
        if table_name not in valid_tables:
            return []
        return self.query(
            f"SELECT * FROM {table_name} WHERE farm_code = ? AND period = ?",
            (farm_code, period)
        )
    
    def save_production_record(self, table_name, data):
        """保存生产记录"""
        field_map = {
            'breeding_record': ['farm_code', 'period', 'breeding_date', 'sow_no', 'boar_no', 
                               'staff_code', 'breeding_type', 'heat_interval', 'remarks'],
            'farrow_record': ['farm_code', 'period', 'farrow_date', 'sow_no', 'total_born',
                             'healthy_piglets', 'weak_piglets', 'dead_piglets', 'mummy', 'staff_code', 'remarks'],
            'weaning_record': ['farm_code', 'period', 'weaning_date', 'sow_no', 'piglet_count',
                              'piglet_weight', 'avg_weight', 'staff_code', 'remarks'],
            'transfer_record': ['farm_code', 'period', 'transfer_date', 'pig_no', 'from_stage',
                              'to_stage', 'head_count', 'total_weight', 'avg_weight', 'transfer_type', 'staff_code', 'remarks'],
            'death_record': ['farm_code', 'period', 'death_date', 'pig_no', 'stage',
                           'head_count', 'weight', 'death_reason', 'staff_code', 'remarks'],
            'cull_record': ['farm_code', 'period', 'cull_date', 'pig_no', 'stage',
                          'head_count', 'weight', 'cull_reason', 'staff_code', 'remarks']
        }
        if table_name not in field_map:
            return
        fields = field_map[table_name]
        placeholders = ','.join(['?' for _ in fields])
        sql = f"INSERT OR REPLACE INTO {table_name} ({','.join(fields)}) VALUES ({placeholders})"
        self.executemany(sql, data)
    
    def log_operation(self, user_id, operation_type, table_name, record_id, old_value, new_value, ip_address=''):
        """记录操作日志"""
        sql = '''
            INSERT INTO operation_log 
            (user_id, operation_type, table_name, record_id, old_value, new_value, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.execute(sql, (user_id, operation_type, table_name, record_id, old_value, new_value, ip_address))
    
    def get_user(self, username):
        """获取用户"""
        result = self.query("SELECT * FROM users WHERE username = ?", (username,))
        return dict(result[0]) if result else None
    
    def get_all_users(self):
        """获取所有用户"""
        return [dict(r) for r in self.query("SELECT * FROM users")]
    
    def save_user(self, username, password, role, farm_codes):
        """保存用户"""
        sql = '''
            INSERT OR REPLACE INTO users (username, password, role, farm_codes)
            VALUES (?, ?, ?, ?)
        '''
        self.execute(sql, (username, password, role, farm_codes))


# 成本科目配置
COST_SUBJECTS = {
    # 直接材料
    '50010206': {'name': '饲料', 'category': '直接材料', 'order': 1},
    '50010225': {'name': '饲料运费', 'category': '直接材料', 'order': 2},
    '50010222': {'name': '精液成本', 'category': '直接材料', 'order': 3},
    # 健康成本
    '50010201': {'name': '消毒费', 'category': '健康成本', 'order': 4},
    '50010202': {'name': '疫苗费', 'category': '健康成本', 'order': 5},
    '50010203': {'name': '口服加药', 'category': '健康成本', 'order': 6},
    '50010204': {'name': '注射药品', 'category': '健康成本', 'order': 7},
    # 直接人工
    '50010101': {'name': '工资薪金', 'category': '直接人工', 'order': 8},
    '50010102': {'name': '职工福利', 'category': '直接人工', 'order': 9},
    '50010103': {'name': '工会经费', 'category': '直接人工', 'order': 10},
    '50010104': {'name': '职工教育', 'category': '直接人工', 'order': 11},
    '50010105': {'name': '五险一金', 'category': '直接人工', 'order': 12},
    # 折旧摊销
    '50010301': {'name': '固定资产折旧', 'category': '折旧摊销', 'order': 13},
    '50010302': {'name': '使用权资产折旧', 'category': '折旧摊销', 'order': 14},
    '50010303': {'name': '种猪折旧', 'category': '折旧摊销', 'order': 15},
    '50010304': {'name': '种猪死亡摊销', 'category': '折旧摊销', 'order': 16},
    '50010305': {'name': '扶贫场租赁费', 'category': '折旧摊销', 'order': 17},
    # 燃料动力
    '50010401': {'name': '电费', 'category': '燃料动力', 'order': 18},
    '50010402': {'name': '水费', 'category': '燃料动力', 'order': 19},
    '50010403': {'name': '燃煤', 'category': '燃料动力', 'order': 20},
    '50010404': {'name': '燃油', 'category': '燃料动力', 'order': 21},
    '50010405': {'name': '燃气', 'category': '燃料动力', 'order': 22},
    # 制造费用
    '50010501': {'name': '备品备件', 'category': '制造费用', 'order': 23},
    '50010502': {'name': '物料消耗', 'category': '制造费用', 'order': 24},
    '50010503': {'name': '劳保费', 'category': '制造费用', 'order': 25},
    '50010504': {'name': '维修费', 'category': '制造费用', 'order': 26},
    # 租赁费用
    '50010601': {'name': '土地租赁', 'category': '租赁费用', 'order': 27},
    '50010602': {'name': '补偿款', 'category': '租赁费用', 'order': 28},
    '50010603': {'name': '其他租赁', 'category': '租赁费用', 'order': 29},
    '50010604': {'name': '租赁折旧', 'category': '租赁费用', 'order': 30},
    # 运输费用
    '50010701': {'name': '生猪运费', 'category': '运输费用', 'order': 31},
    # 服务费用
    '50010801': {'name': '检测费', 'category': '服务费用', 'order': 32},
    '50010802': {'name': '服务费', 'category': '服务费用', 'order': 33},
    # 交通费用
    '50010901': {'name': '车辆费用', 'category': '交通费用', 'order': 34},
    # 办公费用
    '50011001': {'name': '业务招待', 'category': '办公费用', 'order': 35},
    '50011002': {'name': '通讯', 'category': '办公费用', 'order': 36},
    '50011003': {'name': '医疗废弃物', 'category': '办公费用', 'order': 37},
    '50011004': {'name': '办公', 'category': '办公费用', 'order': 38},
    '50011005': {'name': '差旅', 'category': '办公费用', 'order': 39},
    '50011006': {'name': '劳务', 'category': '办公费用', 'order': 40},
    # 期间费用
    '50011101': {'name': '期间费用（总部）', 'category': '期间费用', 'order': 41},
    '50011102': {'name': '期间费用（子公司）', 'category': '期间费用', 'order': 42},
}

# 工段配置
STAGES = ['仔猪', '保育', '育肥', '后备']

# 预警规则
ALERT_RULES = {
    'feed_conversion_rate': {'warning': 3.0, 'critical': 3.5, 'unit': ''},
    'cost_per_kg': {'warning': 15, 'critical': 20, 'unit': '元/kg'},
    'pig_age': {'warning': 180, 'critical': 200, 'unit': '天'},
    'mortality_rate': {'warning': 0.05, 'critical': 0.08, 'unit': '%'},
}
