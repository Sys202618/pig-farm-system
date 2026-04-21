/**
 * 猪场管理系统 - API模块
 */
const BASE = '/api';
let TOKEN = localStorage.getItem('token') || '';
let CURRENT_USER = null;
let CONFIG = null;

// ============ 请求封装 ============
async function request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json' };
    if (TOKEN) headers['Authorization'] = `Bearer ${TOKEN}`;
    
    const res = await fetch(`${BASE}${path}`, { ...options, headers });
    const json = await res.json();
    
    if (json.code === 401) {
        logout();
        throw new Error('登录已过期');
    }
    if (json.code !== 0) throw new Error(json.msg || '请求失败');
    return json;
}

// ============ 认证 ============
async function login(username, password) {
    const json = await request('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    TOKEN = json.data.token;
    CURRENT_USER = json.data;
    localStorage.setItem('token', TOKEN);
    localStorage.setItem('user', JSON.stringify(CURRENT_USER));
    return json.data;
}

function logout() {
    TOKEN = '';
    CURRENT_USER = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    location.reload();
}

function getUser() {
    if (!CURRENT_USER) {
        const u = localStorage.getItem('user');
        if (u) CURRENT_USER = JSON.parse(u);
    }
    return CURRENT_USER;
}

// ============ 配置 ============
async function loadConfig() {
    if (!CONFIG) CONFIG = (await request('/config')).data;
    return CONFIG;
}

// ============ 猪场 ============
async function getFarms() { return (await request('/pig_farms')).data; }
async function getFarm(id) { return (await request(`/pig_farms/${id}`)).data; }
async function createFarm(data) { return request('/pig_farms', { method:'POST', body: JSON.stringify(data) }); }
async function updateFarm(id, data) { return request(`/pig_farms/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteFarm(id) { return request(`/pig_farms/${id}`, { method:'DELETE' }); }

// ============ 猪舍 ============
async function getBarns(farmId) { return (await request(`/barns?farm_id=${farmId || ''}`)).data; }
async function createBarn(data) { return request('/barns', { method:'POST', body: JSON.stringify(data) }); }
async function updateBarn(id, data) { return request(`/barns/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteBarn(id) { return request(`/barns/${id}`, { method:'DELETE' }); }

// ============ 员工 ============
async function getEmployees(farmId) { return (await request(`/employees?farm_id=${farmId || ''}`)).data; }
async function createEmployee(data) { return request('/employees', { method:'POST', body: JSON.stringify(data) }); }
async function updateEmployee(id, data) { return request(`/employees/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteEmployee(id) { return request(`/employees/${id}`, { method:'DELETE' }); }

// ============ 猪群 ============
async function getHerds(farmId) { return (await request(`/herds?farm_id=${farmId || ''}`)).data; }
async function createHerd(data) { return request('/herds', { method:'POST', body: JSON.stringify(data) }); }
async function updateHerd(id, data) { return request(`/herds/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteHerd(id) { return request(`/herds/${id}`, { method:'DELETE' }); }

// ============ 生产记录 ============
async function getBreeding(farmId) { return (await request(`/breeding_records?farm_id=${farmId || ''}`)).data; }
async function createBreeding(data) { return request('/breeding_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateBreeding(id, data) { return request(`/breeding_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteBreeding(id) { return request(`/breeding_records/${id}`, { method:'DELETE' }); }

async function getFarrowing(farmId) { return (await request(`/farrowing_records?farm_id=${farmId || ''}`)).data; }
async function createFarrowing(data) { return request('/farrowing_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateFarrowing(id, data) { return request(`/farrowing_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteFarrowing(id) { return request(`/farrowing_records/${id}`, { method:'DELETE' }); }

async function getWeaning(farmId) { return (await request(`/weaning_records?farm_id=${farmId || ''}`)).data; }
async function createWeaning(data) { return request('/weaning_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateWeaning(id, data) { return request(`/weaning_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteWeaning(id) { return request(`/weaning_records/${id}`, { method:'DELETE' }); }

async function getTransfer(farmId) { return (await request(`/transfer_records?farm_id=${farmId || ''}`)).data; }
async function createTransfer(data) { return request('/transfer_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateTransfer(id, data) { return request(`/transfer_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteTransfer(id) { return request(`/transfer_records/${id}`, { method:'DELETE' }); }

async function getDeath(farmId) { return (await request(`/death_records?farm_id=${farmId || ''}`)).data; }
async function createDeath(data) { return request('/death_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateDeath(id, data) { return request(`/death_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteDeath(id) { return request(`/death_records/${id}`, { method:'DELETE' }); }

async function getSales(farmId) { return (await request(`/sales_records?farm_id=${farmId || ''}`)).data; }
async function createSales(data) { return request('/sales_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateSales(id, data) { return request(`/sales_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteSales(id) { return request(`/sales_records/${id}`, { method:'DELETE' }); }

// ============ 财务 ============
async function getIncome(farmId, month) {
    const params = new URLSearchParams({ farm_id: farmId || '' });
    if (month) params.set('month', month);
    return (await request(`/income_records?${params}`)).data;
}
async function createIncome(data) { return request('/income_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateIncome(id, data) { return request(`/income_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteIncome(id) { return request(`/income_records/${id}`, { method:'DELETE' }); }

async function getCost(farmId, month) {
    const params = new URLSearchParams({ farm_id: farmId || '' });
    if (month) params.set('month', month);
    return (await request(`/cost_records?${params}`)).data;
}
async function createCost(data) { return request('/cost_records', { method:'POST', body: JSON.stringify(data) }); }
async function updateCost(id, data) { return request(`/cost_records/${id}`, { method:'PUT', body: JSON.stringify(data) }); }
async function deleteCost(id) { return request(`/cost_records/${id}`, { method:'DELETE' }); }

// ============ 报表 ============
async function getReport(name, farmId, month) {
    const params = new URLSearchParams({ farm_id: farmId || '' });
    if (month) params.set('month', month);
    return (await request(`/reports/${name}?${params}`)).data;
}

// ============ 导出 ============
async function exportReport(reportType, farmId, month) {
    const params = new URLSearchParams({ farm_id: farmId || '' });
    if (month) params.set('month', month);
    const res = await fetch(`${BASE}/export/${reportType}?${params}`, {
        headers: { 'Authorization': `Bearer ${TOKEN}` }
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${reportType}_${month || 'all'}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
}
