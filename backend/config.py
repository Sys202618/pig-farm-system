# -*- coding: utf-8 -*-
"""猪场生产+财务管理系统 - 配置"""
import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(BASE_DIR)
    DATABASE_PATH = os.path.join(PROJECT_DIR, 'data', 'pig_farm.db')
    EXPORT_PATH = os.path.join(PROJECT_DIR, 'exports')
    SECRET_KEY = 'pig_farm_system_2026'
    PAGE_SIZE = 50

    # 成本大类
    COST_CATEGORIES = [
        '饲料成本', '兽药疫苗成本', '猪精成本', '人工成本',
        '水电费用', '折旧费用', '维修费用', '其他费用'
    ]

    # 收入类型
    INCOME_TYPES = ['生猪销售收入', '种猪销售收入', '仔猪销售收入', '其他收入']

    # 猪只类型
    PIG_TYPES = ['经产母猪', '初产母猪', '公猪', '仔猪', '保育猪', '育肥猪', '后备猪']

    # 猪舍类型
    BARN_TYPES = ['配种舍', '妊娠舍', '分娩舍', '保育舍', '育肥舍', '公猪舍']

    # 配种方式
    BREED_METHODS = ['本交', '人工授精']

    # 死亡类型
    DEATH_TYPES = ['死亡', '淘汰']

    # 员工角色
    EMPLOYEE_ROLES = ['场长', '饲养员', '配种员', '兽医', '财务', '其他']

    # 用户角色
    USER_ROLES = {
        'admin': '管理员',
        'production': '生产员',
        'finance': '财务'
    }
