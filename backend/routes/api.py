# -*- coding: utf-8 -*-
"""
猪场成本核算系统 - API路由
"""
from flask import Blueprint, request, jsonify, session
from datetime import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ..models.database import Database, COST_SUBJECTS, STAGES
from ..services.cost_calculator import CostCalculator

api_bp = Blueprint('api', __name__, url_prefix='/api')

# 全局数据库实例（通过app.py注入）
db = None
calculator = None


def init_api(_db):
    """初始化API模块"""
    global db, calculator
    db = _db
    calculator = CostCalculator(db)


# ========== 辅助函数 ==========

def success(data=None, msg='success'):
    """成功响应"""
    response = {'code': 0, 'msg': msg}
    if data is not None:
        response['data'] = data
    return jsonify(response)


def error(msg='error', code=1):
    """错误响应"""
    return jsonify({'code': code, 'msg': msg})


def parse_params():
    """解析请求参数"""
    data = request.get_json() or request.args.to_dict()
    return data


def check_permission(required_role):
    """检查权限"""
    if 'user' not in session:
        return False
    user = session['user']
    if user.get('role') == 'super_admin':
        return True
    if required_role == 'view':
        return True
    if user.get('role') == required_role:
        return True
    return False


# ========== 认证接口 ==========

@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    data = parse_params()
    username = data.get('username', '')
    password = data.get('password', '')
    
    user = db.get_user(username)
    
    if not user:
        return error('用户不存在')
    
    if user['password'] != password:
        return error('密码错误')
    
    session['user'] = {
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'farm_codes': user['farm_codes'].split(',') if user['farm_codes'] else []
    }
    
    return success({'user': {
        'username': user['username'],
        'role': user['role']
    }})


@api_bp.route('/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.pop('user', None)
    return success()


@api_bp.route('/auth/current', methods=['GET'])
def get_current_user():
    """获取当前用户"""
    if 'user' not in session:
        return error('未登录', code=401)
    return success({'user': session['user']})


# ========== 场次管理 ==========

@api_bp.route('/farms', methods=['GET'])
def get_farms():
    """获取场次列表"""
    user = session.get('user', {})
    farm_codes = user.get('farm_codes', [])
    
    if farm_codes and farm_codes[0]:
        farms = db.get_farms(farm_codes)
    else:
        farms = db.get_farms()
    
    return success([dict(f) for f in farms])


@api_bp.route('/farms/<farm_code>', methods=['GET'])
def get_farm(farm_code):
    """获取单个场次"""
    farm = db.get_farm_by_code(farm_code)
    if not farm:
        return error('场次不存在')
    return success(dict(farm))


@api_bp.route('/farms', methods=['POST'])
def create_farm():
    """创建场次"""
    data = parse_params()
    
    farm_code = data.get('farm_code', '')
    farm_name = data.get('farm_name', '')
    
    if not farm_code or not farm_name:
        return error('场次编码和名称不能为空')
    
    sql = '''
        INSERT INTO pig_farm (farm_code, farm_name, farm_line, region, company)
        VALUES (?, ?, ?, ?, ?)
    '''
    db.execute(sql, (
        farm_code,
        farm_name,
        data.get('farm_line', ''),
        data.get('region', ''),
        data.get('company', '')
    ))
    
    return success(msg='场次创建成功')


# ========== 成本核算接口 ==========

@api_bp.route('/cost/sales', methods=['GET'])
def get_sales_cost():
    """销售成本查询"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    sales_type = request.args.get('sales_type', 'all')
    unit = request.args.get('unit', 'head')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_sales_cost(farm_code, period, sales_type, unit)
    return success(result)


@api_bp.route('/cost/piglet-birth', methods=['GET'])
def get_piglet_birth_cost():
    """仔猪出生成本"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_piglet_birth_cost(farm_code, period)
    return success(result)


@api_bp.route('/cost/weaning', methods=['GET'])
def get_weaning_cost():
    """断奶成本（校正体重）"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    correction_weight = float(request.args.get('correction_weight', 6))
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_weaning_cost(farm_code, period, correction_weight)
    return success(result)


@api_bp.route('/cost/nursery', methods=['GET'])
def get_nursery_cost():
    """保育转出成本（校正体重）"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    correction_weight = float(request.args.get('correction_weight', 28))
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_nursery_cost(farm_code, period, correction_weight)
    return success(result)


@api_bp.route('/cost/weight-gain', methods=['GET'])
def get_weight_gain_cost():
    """增重成本"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    stage = request.args.get('stage', '育肥')
    exclude_death = request.args.get('exclude_death', 'true').lower() == 'true'
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_weight_gain_cost(farm_code, period, stage, exclude_death)
    return success(result)


@api_bp.route('/cost/semen', methods=['GET'])
def get_semen_cost():
    """精液成本"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_semen_cost(farm_code, period)
    return success(result)


@api_bp.route('/cost/breeding-daily', methods=['GET'])
def get_breeding_daily_cost():
    """种猪日成本"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_breeding_daily_cost(farm_code, period)
    return success(result)


@api_bp.route('/cost/finishing', methods=['GET'])
def get_finishing_cost():
    """商品肉猪成本"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_finishing_pig_cost(farm_code, period)
    return success(result)


@api_bp.route('/cost/ranking', methods=['GET'])
def get_transfer_ranking():
    """头均转出成本排名"""
    period = request.args.get('period', '')
    region = request.args.get('region')
    line = request.args.get('line')
    top_n = int(request.args.get('top_n', 10))
    
    if not period:
        return error('月份不能为空')
    
    result = calculator.calc_transfer_cost_ranking(period, region, line, top_n)
    return success(result)


@api_bp.route('/cost/total', methods=['GET'])
def get_total_cost():
    """全成本汇总"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.calc_total_cost_summary(farm_code, period)
    return success(result)


@api_bp.route('/cost/anomalies', methods=['GET'])
def get_anomalies():
    """异常数据检测"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    result = calculator.check_anomalies(farm_code, period)
    return success(result)


# ========== 成本数据管理 ==========

@api_bp.route('/cost/data', methods=['GET'])
def get_cost_data():
    """获取成本数据"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    stage = request.args.get('stage')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    data = db.get_cost_data(farm_code, period, stage)
    return success([dict(d) for d in data])


@api_bp.route('/cost/data', methods=['POST'])
def save_cost_data():
    """保存成本数据"""
    data = parse_params()
    records = data.get('records', [])
    
    if not records:
        return error('没有数据需要保存')
    
    save_data = []
    for r in records:
        save_data.append((
            r.get('farm_code', ''),
            r.get('period', ''),
            r.get('stage', ''),
            r.get('subject_code', ''),
            r.get('subject_name', ''),
            float(r.get('amount', 0)),
            float(r.get('weight', 0)),
            int(r.get('head_count', 0)),
            float(r.get('feed_weight', 0))
        ))
    
    db.save_cost_data(save_data)
    return success(msg='成本数据保存成功')


# ========== 生产数据管理 ==========

@api_bp.route('/production/breeding', methods=['GET'])
def get_breeding_summary():
    """获取繁殖汇总"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    data = db.get_breeding_summary(farm_code, period)
    return success(data)


@api_bp.route('/production/breeding', methods=['POST'])
def save_breeding_summary():
    """保存繁殖汇总"""
    data = parse_params()
    records = data.get('records', [])
    
    save_data = []
    for r in records:
        save_data.append((
            r.get('farm_code', ''),
            r.get('period', ''),
            int(r.get('breeding_count', 0)),
            int(r.get('return_heat_count', 0)),
            int(r.get('empty_check_count', 0)),
            int(r.get('abortion_count', 0)),
            int(r.get('farrow_count', 0)),
            int(r.get('pregnant_sales', 0)),
            int(r.get('total_born', 0)),
            int(r.get('healthy_piglets', 0)),
            int(r.get('weak_piglets', 0))
        ))
    
    db.save_breeding_summary(save_data)
    return success(msg='繁殖汇总保存成功')


@api_bp.route('/production/change', methods=['GET'])
def get_change_summary():
    """获取变动汇总"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    stage = request.args.get('stage')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    data = db.get_change_summary(farm_code, period, stage)
    return success(data)


@api_bp.route('/production/change', methods=['POST'])
def save_change_summary():
    """保存变动汇总"""
    data = parse_params()
    records = data.get('records', [])
    
    save_data = []
    for r in records:
        save_data.append((
            r.get('farm_code', ''),
            r.get('period', ''),
            r.get('stage', ''),
            int(r.get('opening_head', 0)),
            float(r.get('opening_weight', 0)),
            int(r.get('entry_head', 0)),
            float(r.get('entry_weight', 0)),
            int(r.get('transfer_in_head', 0)),
            float(r.get('transfer_in_weight', 0)),
            int(r.get('transfer_out_head', 0)),
            float(r.get('transfer_out_weight', 0)),
            int(r.get('sales_head', 0)),
            float(r.get('sales_weight', 0)),
            int(r.get('death_head', 0)),
            float(r.get('death_weight', 0)),
            int(r.get('cull_head', 0)),
            float(r.get('cull_weight', 0)),
            int(r.get('closing_head', 0)),
            float(r.get('closing_weight', 0)),
            float(r.get('total_feed', 0)),
            float(r.get('total_feed_weight', 0)),
            float(r.get('daily_gain', 0)),
            float(r.get('feed_conversion_rate', 0)),
            float(r.get('mortality_rate', 0))
        ))
    
    db.save_change_summary(save_data)
    return success(msg='变动汇总保存成功')


@api_bp.route('/production/sales', methods=['GET'])
def get_sales_records():
    """获取销售记录"""
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period:
        return error('场次和月份不能为空')
    
    data = db.get_sales_data(farm_code, period)
    return success([dict(d) for d in data])


@api_bp.route('/production/sales', methods=['POST'])
def save_sales_records():
    """保存销售记录"""
    data = parse_params()
    records = data.get('records', [])
    
    save_data = []
    for r in records:
        save_data.append((
            r.get('farm_code', ''),
            r.get('period', ''),
            r.get('sales_date', ''),
            r.get('pig_no', ''),
            r.get('pig_type', ''),
            r.get('sales_type', ''),
            int(r.get('head_count', 0)),
            float(r.get('total_weight', 0)),
            float(r.get('avg_weight', 0)),
            float(r.get('unit_price', 0)),
            float(r.get('total_amount', 0)),
            r.get('staff_code', ''),
            r.get('remarks', '')
        ))
    
    db.save_sales_data(save_data)
    return success(msg='销售记录保存成功')


@api_bp.route('/production/records', methods=['GET'])
def get_production_records():
    """获取生产记录（配种/分娩/断奶/转群/死亡/淘汰）"""
    table_name = request.args.get('table', '')
    farm_code = request.args.get('farm_code', '')
    period = request.args.get('period', '')
    
    if not farm_code or not period or not table_name:
        return error('参数不完整')
    
    data = db.get_production_records(table_name, farm_code, period)
    return success([dict(d) for d in data])


@api_bp.route('/production/records', methods=['POST'])
def save_production_records():
    """保存生产记录"""
    data = parse_params()
    table_name = data.get('table', '')
    records = data.get('records', [])
    
    if not table_name or not records:
        return error('参数不完整')
    
    db.save_production_record(table_name, records)
    return success(msg='生产记录保存成功')


# ========== 数据导入导出 ==========

@api_bp.route('/import/validate', methods=['POST'])
def validate_import():
    """数据导入校验"""
    data = parse_params()
    import_type = data.get('type', '')
    records = data.get('records', [])
    
    validated = []
    errors = []
    
    for i, record in enumerate(records):
        record_errors = []
        
        # 基本校验
        if import_type == 'cost':
            if not record.get('farm_code'):
                record_errors.append('场次编码不能为空')
            if not record.get('period'):
                record_errors.append('月份不能为空')
            if not record.get('stage'):
                record_errors.append('工段不能为空')
            if not record.get('subject_code'):
                record_errors.append('科目编码不能为空')
        
        if record_errors:
            errors.append({'row': i + 1, 'errors': record_errors})
        else:
            validated.append(record)
    
    return success({
        'total': len(records),
        'valid': len(validated),
        'invalid': len(errors),
        'validated': validated,
        'errors': errors
    })


@api_bp.route('/import/execute', methods=['POST'])
def execute_import():
    """执行数据导入"""
    data = parse_params()
    import_type = data.get('type', '')
    records = data.get('records', [])
    
    if not records:
        return error('没有数据需要导入')
    
    if import_type == 'cost':
        db.save_cost_data([
            (
                r.get('farm_code', ''),
                r.get('period', ''),
                r.get('stage', ''),
                r.get('subject_code', ''),
                r.get('subject_name', ''),
                float(r.get('amount', 0)),
                float(r.get('weight', 0)),
                int(r.get('head_count', 0)),
                float(r.get('feed_weight', 0))
            ) for r in records
        ])
    elif import_type == 'breeding':
        db.save_breeding_summary([
            (
                r.get('farm_code', ''),
                r.get('period', ''),
                int(r.get('breeding_count', 0)),
                int(r.get('return_heat_count', 0)),
                int(r.get('empty_check_count', 0)),
                int(r.get('abortion_count', 0)),
                int(r.get('farrow_count', 0)),
                int(r.get('pregnant_sales', 0)),
                int(r.get('total_born', 0)),
                int(r.get('healthy_piglets', 0)),
                int(r.get('weak_piglets', 0))
            ) for r in records
        ])
    elif import_type == 'change':
        db.save_change_summary([
            (
                r.get('farm_code', ''),
                r.get('period', ''),
                r.get('stage', ''),
                int(r.get('opening_head', 0)),
                float(r.get('opening_weight', 0)),
                int(r.get('entry_head', 0)),
                float(r.get('entry_weight', 0)),
                int(r.get('transfer_in_head', 0)),
                float(r.get('transfer_in_weight', 0)),
                int(r.get('transfer_out_head', 0)),
                float(r.get('transfer_out_weight', 0)),
                int(r.get('sales_head', 0)),
                float(r.get('sales_weight', 0)),
                int(r.get('death_head', 0)),
                float(r.get('death_weight', 0)),
                int(r.get('cull_head', 0)),
                float(r.get('cull_weight', 0)),
                int(r.get('closing_head', 0)),
                float(r.get('closing_weight', 0)),
                float(r.get('total_feed', 0)),
                float(r.get('total_feed_weight', 0)),
                float(r.get('daily_gain', 0)),
                float(r.get('feed_conversion_rate', 0)),
                float(r.get('mortality_rate', 0))
            ) for r in records
        ])
    elif import_type == 'sales':
        db.save_sales_data([
            (
                r.get('farm_code', ''),
                r.get('period', ''),
                r.get('sales_date', ''),
                r.get('pig_no', ''),
                r.get('pig_type', ''),
                r.get('sales_type', ''),
                int(r.get('head_count', 0)),
                float(r.get('total_weight', 0)),
                float(r.get('avg_weight', 0)),
                float(r.get('unit_price', 0)),
                float(r.get('total_amount', 0)),
                r.get('staff_code', ''),
                r.get('remarks', '')
            ) for r in records
        ])
    
    return success({'imported': len(records)}, msg=f'成功导入{len(records)}条数据')


# ========== 基础数据接口 ==========

@api_bp.route('/dictionary/stages', methods=['GET'])
def get_stages():
    """获取工段列表"""
    return success(STAGES)


@api_bp.route('/dictionary/subjects', methods=['GET'])
def get_subjects():
    """获取成本科目"""
    category = request.args.get('category')
    
    result = []
    for code, info in COST_SUBJECTS.items():
        if category and info['category'] != category:
            continue
        result.append({
            'code': code,
            'name': info['name'],
            'category': info['category']
        })
    
    return success(result)


@api_bp.route('/dictionary/subjects/all', methods=['GET'])
def get_all_subjects():
    """获取所有科目（含分类）"""
    categories = {}
    for code, info in COST_SUBJECTS.items():
        cat = info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            'code': code,
            'name': info['name']
        })
    
    return success([
        {'category': cat, 'subjects': subjects}
        for cat, subjects in categories.items()
    ])


# ========== 用户管理 ==========

@api_bp.route('/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    users = db.get_all_users()
    for u in users:
        u.pop('password', None)
    return success(users)


@api_bp.route('/users', methods=['POST'])
def create_user():
    """创建用户"""
    data = parse_params()
    
    username = data.get('username', '')
    password = data.get('password', '123456')
    role = data.get('role', 'dept_view')
    farm_codes = data.get('farm_codes', '')
    
    if not username:
        return error('用户名不能为空')
    
    db.save_user(username, password, role, farm_codes)
    return success(msg='用户创建成功')


# ========== 系统接口 ==========

@api_bp.route('/system/periods', methods=['GET'])
def get_periods():
    """获取可选月份"""
    # 生成最近24个月的选项
    from datetime import datetime
    periods = []
    now = datetime.now()
    for i in range(24):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        periods.append(f"{year}-{month:02d}")
    return success(periods)


@api_bp.route('/system/backup', methods=['POST'])
def backup_database():
    """数据库备份"""
    import shutil
    from ..config import Config
    
    backup_path = Config.DATABASE_PATH + f".backup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    shutil.copy2(Config.DATABASE_PATH, backup_path)
    
    return success({'backup_path': backup_path}, msg='数据库备份成功')


@api_bp.route('/system/logs', methods=['GET'])
def get_operation_logs():
    """获取操作日志"""
    limit = int(request.args.get('limit', 100))
    
    logs = db.query(
        f"SELECT * FROM operation_log ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    
    return success([dict(log) for log in logs])
