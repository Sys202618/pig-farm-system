# -*- coding: utf-8 -*-
"""
猪场成本核算系统 - 核心成本计算引擎
100% 实现用户提供的所有计算公式
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from .database import Database, COST_SUBJECTS, STAGES, ALERT_RULES


class CostCalculator:
    """成本计算引擎"""
    
    def __init__(self, db: Database):
        self.db = db
        self._zero = Decimal('0')
        self._scale = Decimal('0.0001')
    
    def _d(self, value):
        """转换为Decimal，None或空值返回0"""
        if value is None or value == '':
            return self._zero
        try:
            return Decimal(str(value))
        except:
            return self._zero
    
    def _round(self, value, scale=4):
        """四舍五入"""
        d = self._d(value)
        return d.quantize(Decimal(str(scale)), rounding=ROUND_HALF_UP)
    
    def _round2(self, value):
        """保留2位小数"""
        return self._round(value, 2)
    
    # ========== 1. 销售成本计算 ==========
    def calc_sales_cost(self, farm_code, period, sales_type='all', unit='head'):
        """
        销售成本计算
        
        公式：
        均重 = 销售总重量 ÷ 销售头数
        料价 =（前阶段饲料成本 + 本阶段饲料成本）÷（前阶段料重 + 本阶段料重）
        料比 =（前阶段料重 + 本阶段料重）÷ 销售总重量
        公斤成本 = 对应科目成本 ÷ 销售重量
        头均成本 = 对应科目成本 ÷ 销售头数
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'sales_type': sales_type,
            'unit': unit,
            'basic_info': {},
            'cost_by_subject': [],
            'total_cost': self._zero,
            'warnings': []
        }
        
        # 获取销售数据
        sales_data = self.db.get_sales_data(farm_code, period)
        
        if not sales_data:
            return result
        
        # 筛选销售类型
        if sales_type != 'all':
            sales_data = [s for s in sales_data if s['sales_type'] == sales_type]
        
        if not sales_data:
            return result
        
        # 计算基本指标
        total_head = sum(s['head_count'] for s in sales_data)
        total_weight = sum(s['total_weight'] for s in sales_data)
        avg_weight = total_weight / total_head if total_head > 0 else self._zero
        
        result['basic_info'] = {
            'total_head': total_head,
            'total_weight': self._round2(total_weight),
            'avg_weight': self._round2(avg_weight)
        }
        
        # 获取各工段成本数据
        stage_costs = {}
        for stage in STAGES:
            cost_data = self.db.get_cost_data(farm_code, period, stage)
            stage_costs[stage] = {row['subject_code']: row for row in cost_data}
        
        # 计算各科目成本
        for code, info in COST_SUBJECTS.items():
            subject_amount = self._zero
            for stage in STAGES:
                if code in stage_costs[stage]:
                    subject_amount += self._d(stage_costs[stage][code]['amount'])
            
            if subject_amount > 0:
                # 计算公斤成本和头均成本
                cost_per_kg = subject_amount / total_weight if total_weight > 0 else self._zero
                cost_per_head = subject_amount / total_head if total_head > 0 else self._zero
                
                cost_item = {
                    'subject_code': code,
                    'subject_name': info['name'],
                    'category': info['category'],
                    'amount': self._round2(subject_amount),
                    'cost_per_kg': self._round2(cost_per_kg),
                    'cost_per_head': self._round2(cost_per_head)
                }
                
                # 预警检查
                if cost_per_kg > ALERT_RULES['cost_per_kg']['critical']:
                    cost_item['warning'] = 'critical'
                    result['warnings'].append(f"{info['name']}公斤成本超标: {cost_item['cost_per_kg']}元/kg")
                
                result['cost_by_subject'].append(cost_item)
                result['total_cost'] += subject_amount
        
        # 计算料价和料比
        self._calc_feed_metrics(result, stage_costs, total_weight)
        
        return result
    
    def _calc_feed_metrics(self, result, stage_costs, sales_weight):
        """计算料价和料比"""
        # 饲料科目编码
        feed_code = '50010206'
        feed_freight_code = '50010225'
        
        # 获取当前和前月数据
        current_period = result['period']
        prev_period = self._get_prev_period(current_period)
        
        # 计算饲料成本和料重
        feed_cost = self._zero
        feed_weight = self._zero
        
        for stage in STAGES:
            # 当前月
            if feed_code in stage_costs[stage]:
                feed_cost += self._d(stage_costs[stage][feed_code]['amount'])
                feed_weight += self._d(stage_costs[stage][feed_code]['feed_weight'])
            # 前月
            prev_data = self.db.get_cost_data(result['farm_code'], prev_period, stage)
            prev_dict = {row['subject_code']: row for row in prev_data}
            if feed_code in prev_dict:
                feed_cost += self._d(prev_dict[feed_code]['amount'])
                feed_weight += self._d(prev_dict[feed_code]['feed_weight'])
        
        # 计算料价 = 饲料成本 / 料重
        feed_price = feed_cost / feed_weight if feed_weight > 0 else self._zero
        
        # 计算料比 = 料重 / 销售总重量
        feed_ratio = feed_weight / sales_weight if sales_weight > 0 else self._zero
        
        result['basic_info']['feed_price'] = self._round2(feed_price)
        result['basic_info']['feed_ratio'] = self._round2(feed_ratio)
        
        # 料比预警
        if feed_ratio > ALERT_RULES['feed_conversion_rate']['critical']:
            result['basic_info']['feed_ratio_warning'] = 'critical'
            result['warnings'].append(f"料比超标: {result['basic_info']['feed_ratio']}")
    
    def _get_prev_period(self, period):
        """获取上一期"""
        try:
            year, month = period.split('-')
            year, month = int(year), int(month)
            if month == 1:
                return f"{year-1}-12"
            else:
                return f"{year}-{month-1:02d}"
        except:
            return period
    
    # ========== 2. 仔猪出生成本计算 ==========
    def calc_piglet_birth_cost(self, farm_code, period):
        """
        仔猪出生成本计算
        
        公式：
        配准率 =（配种头数 − 返情 − 检空）÷ 配种头数
        分娩率 =（分娩母猪 + 怀孕销售）÷ 配种头数
        窝均健仔 = 健仔数 ÷ 产仔母猪数
        仔猪头均出生成本 = 待产转出成本 ÷ 活仔数
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'breeding_metrics': {},
            'farrow_metrics': {},
            'piglet_cost': {},
            'warnings': []
        }
        
        # 获取繁殖汇总数据
        breeding = self.db.get_breeding_summary(farm_code, period)
        
        if not breeding:
            return result
        
        b = {k: self._d(breeding.get(k, 0)) for k in breeding.keys() if breeding.get(k) is not None}
        
        # 配准率计算
        breeding_count = b.get('breeding_count', self._zero)
        return_heat = b.get('return_heat_count', self._zero)
        empty_check = b.get('empty_check_count', self._zero)
        
        confirmed = breeding_count - return_heat - empty_check
        conception_rate = confirmed / breeding_count if breeding_count > 0 else self._zero
        
        # 分娩率计算
        farrow_count = b.get('farrow_count', self._zero)
        pregnant_sales = b.get('pregnant_sales', self._zero)
        farrow_rate = (farrow_count + pregnant_sales) / breeding_count if breeding_count > 0 else self._zero
        
        result['breeding_metrics'] = {
            'breeding_count': int(breeding_count),
            'return_heat': int(return_heat),
            'empty_check': int(empty_check),
            'confirmed': int(confirmed),
            'conception_rate': self._round2(conception_rate * 100),
            'farrow_rate': self._round2(farrow_rate * 100)
        }
        
        # 窝均健仔
        total_born = b.get('total_born', self._zero)
        healthy_piglets = b.get('healthy_piglets', self._zero)
        weak_piglets = b.get('weak_piglets', self._zero)
        
        piglets_per_litter = healthy_piglets / farrow_count if farrow_count > 0 else self._zero
        livability = healthy_piglets / total_born if total_born > 0 else self._zero
        
        result['farrow_metrics'] = {
            'farrow_count': int(farrow_count),
            'total_born': int(total_born),
            'healthy_piglets': int(healthy_piglets),
            'weak_piglets': int(weak_piglets),
            'piglets_per_litter': self._round2(piglets_per_litter),
            'livability': self._round2(livability * 100)
        }
        
        # 仔猪头均出生成本
        # 待产阶段转出成本
        nursing_costs = self.db.get_cost_data(farm_code, period, '仔猪')
        nursing_total = sum(self._d(c['amount']) for c in nursing_costs)
        
        # 活仔数 = 健仔 + 弱仔
        live_piglets = healthy_piglets + weak_piglets
        
        cost_per_piglet = nursing_total / live_piglets if live_piglets > 0 else self._zero
        
        result['piglet_cost'] = {
            'nursing_cost': self._round2(nursing_total),
            'live_piglets': int(live_piglets),
            'cost_per_piglet': self._round2(cost_per_piglet)
        }
        
        return result
    
    # ========== 3. 断奶成本计算（校正体重） ==========
    def calc_weaning_cost(self, farm_code, period, correction_weight=6):
        """
        断奶成本计算（校正体重）
        
        公式：
        断奶成本 = 实际头均成本 +（校正体重 − 实际均重）× 哺乳段单位增重成本
        
        统计范围：转出 + 内销 + 外销，剔除同段转群
        
        参数：
        - correction_weight: 校正体重（6kg 或 7kg）
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'correction_weight': correction_weight,
            'actual': {},
            'corrected': {},
            'warnings': []
        }
        
        # 获取仔猪转出数据（剔除同段转群）
        transfer_data = self.db.query('''
            SELECT * FROM piglet_transfer 
            WHERE farm_code = ? AND period = ? AND transfer_type != '同段转群'
        ''', (farm_code, period))
        
        if not transfer_data:
            return result
        
        # 计算实际数据
        total_head = sum(t['head_count'] for t in transfer_data)
        total_weight = sum(t['total_weight'] for t in transfer_data)
        total_cost = sum(t['total_cost'] for t in transfer_data)
        
        actual_avg_weight = total_weight / total_head if total_head > 0 else self._zero
        actual_cost_per_head = total_cost / total_head if total_head > 0 else self._zero
        
        result['actual'] = {
            'total_head': int(total_head),
            'total_weight': self._round2(total_weight),
            'avg_weight': self._round2(actual_avg_weight),
            'cost_per_head': self._round2(actual_cost_per_head)
        }
        
        # 获取哺乳段变动汇总，计算单位增重成本
        change_data = self.db.get_change_summary(farm_code, period, '仔猪')
        
        if change_data:
            change = change_data[0]
            nursing_cost = self._d(change.get('closing_weight', 0)) - self._d(change.get('opening_weight', 0))
            
            # 哺乳段增重 = 期末重量 - 期初重量 - 入栏重量
            opening_weight = self._d(change.get('opening_weight', 0))
            entry_weight = self._d(change.get('entry_weight', 0))
            closing_weight = self._d(change.get('closing_weight', 0))
            
            # 获取哺乳段总成本
            nursing_costs = self.db.get_cost_data(farm_code, period, '仔猪')
            nursing_total_cost = sum(self._d(c['amount']) for c in nursing_costs)
            
            # 单位增重成本 = 哺乳段总成本 / 哺乳段增重
            weight_gain = closing_weight - opening_weight - entry_weight
            cost_per_kg_gain = nursing_total_cost / weight_gain if weight_gain > 0 else self._zero
            
            result['actual']['weight_gain'] = self._round2(weight_gain)
            result['actual']['cost_per_kg_gain'] = self._round2(cost_per_kg_gain)
            
            # 计算校正成本
            weight_diff = self._d(correction_weight) - actual_avg_weight
            correction_amount = weight_diff * cost_per_kg_gain
            corrected_cost = actual_cost_per_head + correction_amount
            
            result['corrected'] = {
                'weight_diff': self._round2(weight_diff),
                'correction_amount': self._round2(correction_amount),
                'corrected_cost': self._round2(corrected_cost)
            }
            
            # 预警检查
            if corrected_cost > Decimal('500'):
                result['warnings'].append(f"断奶校正成本偏高: {corrected_cost}元/头")
        else:
            result['warnings'].append("未获取到哺乳段变动数据")
        
        return result
    
    # ========== 4. 保育转出成本计算（校正体重） ==========
    def calc_nursery_cost(self, farm_code, period, correction_weight=28):
        """
        保育转出成本计算（校正体重）
        
        公式：
        保育成本 = 实际头均成本 +（校正体重 − 转出均重）× 保育单位增重成本
        
        统计范围：转出 + 内销，剔除同段转群
        
        参数：
        - correction_weight: 校正体重（28kg、29kg 或 30kg）
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'correction_weight': correction_weight,
            'actual': {},
            'corrected': {},
            'warnings': []
        }
        
        # 获取保育转出数据（转出 + 内销，剔除同段转群）
        transfer_data = self.db.query('''
            SELECT * FROM piglet_transfer 
            WHERE farm_code = ? AND period = ? AND transfer_type IN ('转出', '内销')
        ''', (farm_code, period))
        
        if not transfer_data:
            return result
        
        # 计算实际数据
        total_head = sum(t['head_count'] for t in transfer_data)
        total_weight = sum(t['total_weight'] for t in transfer_data)
        total_cost = sum(t['total_cost'] for t in transfer_data)
        
        actual_avg_weight = total_weight / total_head if total_head > 0 else self._zero
        actual_cost_per_head = total_cost / total_head if total_head > 0 else self._zero
        
        result['actual'] = {
            'total_head': int(total_head),
            'total_weight': self._round2(total_weight),
            'avg_weight': self._round2(actual_avg_weight),
            'cost_per_head': self._round2(actual_cost_per_head)
        }
        
        # 获取保育段变动汇总，计算单位增重成本
        change_data = self.db.get_change_summary(farm_code, period, '保育')
        
        if change_data:
            change = change_data[0]
            
            opening_weight = self._d(change.get('opening_weight', 0))
            entry_weight = self._d(change.get('entry_weight', 0))
            closing_weight = self._d(change.get('closing_weight', 0))
            
            # 获取保育段总成本
            nursery_costs = self.db.get_cost_data(farm_code, period, '保育')
            nursery_total_cost = sum(self._d(c['amount']) for c in nursery_costs)
            
            # 保育段增重
            weight_gain = closing_weight - opening_weight - entry_weight
            cost_per_kg_gain = nursery_total_cost / weight_gain if weight_gain > 0 else self._zero
            
            result['actual']['weight_gain'] = self._round2(weight_gain)
            result['actual']['cost_per_kg_gain'] = self._round2(cost_per_kg_gain)
            
            # 计算校正成本
            weight_diff = self._d(correction_weight) - actual_avg_weight
            correction_amount = weight_diff * cost_per_kg_gain
            corrected_cost = actual_cost_per_head + correction_amount
            
            result['corrected'] = {
                'weight_diff': self._round2(weight_diff),
                'correction_amount': self._round2(correction_amount),
                'corrected_cost': self._round2(corrected_cost)
            }
            
            # 预警检查
            if corrected_cost > Decimal('1500'):
                result['warnings'].append(f"保育校正成本偏高: {corrected_cost}元/头")
        else:
            result['warnings'].append("未获取到保育段变动数据")
        
        return result
    
    # ========== 5. 增重成本计算 ==========
    def calc_weight_gain_cost(self, farm_code, period, stage, exclude_death=True):
        """
        增重成本计算
        
        公式：
        料肉比 = 料重 ÷ 增重
        含死亡增重成本 = 生产成本 ÷ 总增重
        不含死亡增重成本 = 生产成本 ÷（总增重 − 死亡增重）
        
        参数：
        - exclude_death: 是否排除死亡（True=不含死亡，False=含死亡）
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'stage': stage,
            'metrics': {},
            'warnings': []
        }
        
        # 获取变动汇总数据
        change_data = self.db.get_change_summary(farm_code, period, stage)
        
        if not change_data:
            return result
        
        change = change_data[0]
        
        # 获取阶段成本数据
        stage_costs = self.db.get_cost_data(farm_code, period, stage)
        total_cost = sum(self._d(c['amount']) for c in stage_costs)
        total_feed_weight = sum(self._d(c['feed_weight']) for c in stage_costs)
        
        # 计算增重
        opening_weight = self._d(change.get('opening_weight', 0))
        entry_weight = self._d(change.get('entry_weight', 0))
        closing_weight = self._d(change.get('closing_weight', 0))
        death_weight = self._d(change.get('death_weight', 0))
        
        total_gain = closing_weight - opening_weight - entry_weight
        gain_exclude_death = total_gain - death_weight
        
        # 料肉比 = 料重 ÷ 增重
        feed_ratio = total_feed_weight / total_gain if total_gain > 0 else self._zero
        
        # 含死亡增重成本
        cost_per_kg_including_death = total_cost / total_gain if total_gain > 0 else self._zero
        
        # 不含死亡增重成本
        cost_per_kg_excluding_death = total_cost / gain_exclude_death if gain_exclude_death > 0 else self._zero
        
        result['metrics'] = {
            'total_cost': self._round2(total_cost),
            'total_feed_weight': self._round2(total_feed_weight),
            'total_gain': self._round2(total_gain),
            'death_weight': self._round2(death_weight),
            'gain_exclude_death': self._round2(gain_exclude_death),
            'feed_ratio': self._round2(feed_ratio),
            'cost_per_kg_including_death': self._round2(cost_per_kg_including_death),
            'cost_per_kg_excluding_death': self._round2(cost_per_kg_excluding_death),
            'cost_per_kg': self._round2(cost_per_kg_excluding_death if exclude_death else cost_per_kg_including_death)
        }
        
        # 预警检查
        if feed_ratio > ALERT_RULES['feed_conversion_rate']['critical']:
            result['warnings'].append(f"料比超标: {feed_ratio}")
            result['metrics']['feed_ratio_warning'] = 'critical'
        
        return result
    
    # ========== 6. 精液成本计算 ==========
    def calc_semen_cost(self, farm_code, period):
        """
        精液成本计算
        
        公式：
        公猪平均存栏 = 饲养头日数 ÷ 天数
        精液份数 = 场内接收 + 外销
        头均精液份数 = 总份数 ÷ 平均存栏
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'metrics': {},
            'cost_breakdown': []
        }
        
        # 获取精液生产数据
        semen_data = self.db.query('''
            SELECT * FROM semen_production WHERE farm_code = ? AND period = ?
        ''', (farm_code, period))
        
        if not semen_data:
            return result
        
        semen = semen_data[0]
        
        avg_stock = self._d(semen.get('avg_stock', 0))
        total_semen = self._d(semen.get('total_semen', 0))
        internal_use = self._d(semen.get('internal_use', 0))
        external_sales = self._d(semen.get('external_sales', 0))
        production_cost = self._d(semen.get('production_cost', 0))
        
        # 计算头均精液份数
        semen_per_boar = total_semen / avg_stock if avg_stock > 0 else self._zero
        
        # 获取精液成本数据
        semen_cost_data = self.db.get_cost_data(farm_code, period, '仔猪')  # 精液成本计入仔猪阶段
        semen_cost = sum(
            self._d(c['amount']) for c in semen_cost_data 
            if c['subject_code'] == '50010222'
        )
        
        # 头均精液成本
        cost_per_semen = semen_cost / total_semen if total_semen > 0 else self._zero
        cost_per_boar = semen_cost / avg_stock if avg_stock > 0 else self._zero
        
        result['metrics'] = {
            'avg_stock': self._round2(avg_stock),
            'total_semen': int(total_semen),
            'internal_use': int(internal_use),
            'external_sales': int(external_sales),
            'semen_per_boar': self._round2(semen_per_boar),
            'production_cost': self._round2(production_cost),
            'semen_cost': self._round2(semen_cost),
            'cost_per_semen': self._round2(cost_per_semen),
            'cost_per_boar': self._round2(cost_per_boar)
        }
        
        return result
    
    # ========== 7. 种猪日成本计算 ==========
    def calc_breeding_daily_cost(self, farm_code, period):
        """
        种猪日成本计算
        
        公式：
        日成本 = 当期成本 ÷ 饲养头日数
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'stages': {},
            'total': {},
            'warnings': []
        }
        
        # 获取种猪存栏数据
        stock_data = self.db.query('''
            SELECT * FROM breeding_stock WHERE farm_code = ? AND period = ?
        ''', (farm_code, period))
        
        total_cost = self._zero
        total_head_days = 0
        
        for stock in stock_data:
            stage = stock['stage']
            head_count = self._d(stock.get('head_count', 0))
            head_days = int(stock.get('head_days', 0))
            
            # 获取该阶段成本
            stage_costs = self.db.get_cost_data(farm_code, period, stage)
            cost = sum(self._d(c['amount']) for c in stage_costs)
            
            # 计算日成本
            daily_cost = cost / head_days if head_days > 0 else self._zero
            cost_per_head = cost / head_count if head_count > 0 else self._zero
            
            result['stages'][stage] = {
                'head_count': int(head_count),
                'head_days': head_days,
                'total_cost': self._round2(cost),
                'daily_cost': self._round2(daily_cost),
                'cost_per_head': self._round2(cost_per_head)
            }
            
            total_cost += cost
            total_head_days += head_days
        
        # 汇总
        result['total'] = {
            'total_cost': self._round2(total_cost),
            'total_head_days': total_head_days,
            'avg_daily_cost': self._round2(total_cost / total_head_days if total_head_days > 0 else self._zero)
        }
        
        return result
    
    # ========== 8. 商品肉猪成本分析 ==========
    def calc_finishing_pig_cost(self, farm_code, period):
        """
        商品肉猪成本分析
        
        综合计算：保育 + 育肥 + 后备的成本
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'stages': {},
            'total': {},
            'warnings': []
        }
        
        # 计算各阶段成本
        stages_to_calc = ['保育', '育肥', '后备']
        
        for stage in stages_to_calc:
            # 获取变动汇总
            change_data = self.db.get_change_summary(farm_code, period, stage)
            if change_data:
                change = change_data[0]
                closing_head = int(change.get('closing_head', 0))
                closing_weight = self._d(change.get('closing_weight', 0))
                
                # 获取阶段成本
                stage_costs = self.db.get_cost_data(farm_code, period, stage)
                total_cost = sum(self._d(c['amount']) for c in stage_costs)
                
                # 计算头均和公斤成本
                cost_per_head = total_cost / closing_head if closing_head > 0 else self._zero
                cost_per_kg = total_cost / closing_weight if closing_weight > 0 else self._zero
                
                result['stages'][stage] = {
                    'closing_head': closing_head,
                    'closing_weight': self._round2(closing_weight),
                    'total_cost': self._round2(total_cost),
                    'cost_per_head': self._round2(cost_per_head),
                    'cost_per_kg': self._round2(cost_per_kg)
                }
                
                result['total']['total_cost'] = result['total'].get('total_cost', self._zero) + total_cost
                result['total']['total_head'] = result['total'].get('total_head', 0) + closing_head
                result['total']['total_weight'] = result['total'].get('total_weight', self._zero) + closing_weight
        
        # 计算综合成本
        total_cost = result['total'].get('total_cost', self._zero)
        total_head = result['total'].get('total_head', 0)
        total_weight = result['total'].get('total_weight', self._zero)
        
        result['total'] = {
            'total_cost': self._round2(total_cost),
            'total_head': total_head,
            'total_weight': self._round2(total_weight),
            'cost_per_head': self._round2(total_cost / total_head if total_head > 0 else self._zero),
            'cost_per_kg': self._round2(total_cost / total_weight if total_weight > 0 else self._zero)
        }
        
        return result
    
    # ========== 9. 头均转出成本排名 ==========
    def calc_transfer_cost_ranking(self, period, region=None, line=None, top_n=10):
        """
        头均转出成本排名
        
        按头均转出成本降序排名
        """
        result = {
            'period': period,
            'region': region,
            'line': line,
            'ranking': [],
            'warnings': []
        }
        
        # 构建查询条件
        where_clauses = ["pt.period = ?"]
        params = [period]
        
        if region:
            where_clauses.append("pf.region = ?")
            params.append(region)
        
        if line:
            where_clauses.append("pf.farm_line = ?")
            params.append(line)
        
        where_sql = " AND ".join(where_clauses)
        
        # 查询数据
        sql = f'''
            SELECT 
                pf.farm_code,
                pf.farm_name,
                pf.farm_line,
                pf.region,
                pf.company,
                SUM(pt.head_count) as total_head,
                SUM(pt.total_cost) as total_cost,
                SUM(pt.total_cost) / SUM(pt.head_count) as cost_per_head
            FROM piglet_transfer pt
            JOIN pig_farm pf ON pt.farm_code = pf.farm_code
            WHERE {where_sql} AND pt.transfer_type NOT IN ('同段转群', '转出至育肥')
            GROUP BY pf.farm_code
            ORDER BY cost_per_head DESC
            LIMIT ?
        '''
        params.append(top_n)
        
        ranking_data = self.db.query(sql, params)
        
        for rank, row in enumerate(ranking_data, 1):
            item = {
                'rank': rank,
                'farm_code': row['farm_code'],
                'farm_name': row['farm_name'],
                'farm_line': row['farm_line'],
                'region': row['region'],
                'company': row['company'],
                'total_head': int(row['total_head']) if row['total_head'] else 0,
                'total_cost': self._round2(row['total_cost']) if row['total_cost'] else self._zero,
                'cost_per_head': self._round2(row['cost_per_head']) if row['cost_per_head'] else self._zero
            }
            
            # 预警：成本高于平均值20%标记
            if row['cost_per_head'] and len(ranking_data) > 1:
                avg_cost = sum(self._d(r['cost_per_head']) for r in ranking_data) / len(ranking_data)
                if self._d(row['cost_per_head']) > avg_cost * Decimal('1.2'):
                    item['warning'] = 'high_cost'
                    result['warnings'].append(f"{item['farm_name']}成本高于平均20%")
            
            result['ranking'].append(item)
        
        return result
    
    # ========== 10. 多月平均计算 ==========
    def calc_multi_period_average(self, farm_code, periods, calculator_func, **kwargs):
        """
        多月平均计算
        
        参数：
        - farm_code: 场次编码
        - periods: 月份列表
        - calculator_func: 计算函数
        - **kwargs: 传递给计算函数的其他参数
        """
        results = []
        
        for period in periods:
            result = calculator_func(farm_code, period, **kwargs)
            results.append(result)
        
        # 计算平均值
        avg_result = {
            'farm_code': farm_code,
            'periods': periods,
            'count': len(periods),
            'averages': {}
        }
        
        if not results:
            return avg_result
        
        # 提取数值字段并计算平均
        numeric_fields = ['total_cost', 'avg_weight', 'cost_per_head', 'cost_per_kg']
        
        for field in numeric_fields:
            values = []
            for r in results:
                if isinstance(r, dict):
                    if 'basic_info' in r and field in r['basic_info']:
                        values.append(self._d(r['basic_info'][field]))
                    elif field in r:
                        values.append(self._d(r[field]))
            
            if values:
                avg_result['averages'][field] = self._round2(sum(values) / len(values))
        
        return avg_result
    
    # ========== 11. 全成本汇总计算 ==========
    def calc_total_cost_summary(self, farm_code, period):
        """
        全成本汇总
        
        汇总所有科目、所有工段的成本
        """
        result = {
            'farm_code': farm_code,
            'period': period,
            'by_category': {},
            'by_stage': {},
            'total': self._zero,
            'warnings': []
        }
        
        # 按类别汇总
        category_totals = {}
        for code, info in COST_SUBJECTS.items():
            category = info['category']
            if category not in category_totals:
                category_totals[category] = self._zero
        
        # 按工段汇总
        stage_totals = {stage: self._zero for stage in STAGES}
        
        # 遍历所有工段
        for stage in STAGES:
            cost_data = self.db.get_cost_data(farm_code, period, stage)
            
            for row in cost_data:
                amount = self._d(row['amount'])
                code = row['subject_code']
                
                # 按工段汇总
                stage_totals[stage] += amount
                
                # 按类别汇总
                if code in COST_SUBJECTS:
                    category = COST_SUBJECTS[code]['category']
                    category_totals[category] += amount
                
                # 总计
                result['total'] += amount
        
        result['by_category'] = {k: self._round2(v) for k, v in category_totals.items()}
        result['by_stage'] = {k: self._round2(v) for k, v in stage_totals.items()}
        result['total'] = self._round2(result['total'])
        
        return result
    
    # ========== 12. 异常数据检测 ==========
    def check_anomalies(self, farm_code, period):
        """
        异常数据检测
        
        返回所有异常项
        """
        anomalies = {
            'farm_code': farm_code,
            'period': period,
            'items': []
        }
        
        for stage in STAGES:
            # 检查变动汇总
            change_data = self.db.get_change_summary(farm_code, period, stage)
            if change_data:
                change = change_data[0]
                
                # 料比异常
                feed_ratio = self._d(change.get('feed_conversion_rate', 0))
                if feed_ratio > ALERT_RULES['feed_conversion_rate']['critical']:
                    anomalies['items'].append({
                        'type': 'feed_ratio',
                        'stage': stage,
                        'value': str(feed_ratio),
                        'threshold': str(ALERT_RULES['feed_conversion_rate']['critical']),
                        'severity': 'critical'
                    })
                elif feed_ratio > ALERT_RULES['feed_conversion_rate']['warning']:
                    anomalies['items'].append({
                        'type': 'feed_ratio',
                        'stage': stage,
                        'value': str(feed_ratio),
                        'threshold': str(ALERT_RULES['feed_conversion_rate']['warning']),
                        'severity': 'warning'
                    })
                
                # 死亡率异常
                mortality = self._d(change.get('mortality_rate', 0))
                if mortality > ALERT_RULES['mortality_rate']['critical']:
                    anomalies['items'].append({
                        'type': 'mortality',
                        'stage': stage,
                        'value': str(self._round2(mortality * 100)) + '%',
                        'threshold': str(ALERT_RULES['mortality_rate']['critical'] * 100) + '%',
                        'severity': 'critical'
                    })
        
        return anomalies
