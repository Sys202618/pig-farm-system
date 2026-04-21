/**
 * 猪场管理系统 - 主应用逻辑
 */
let currentPage = 'home';
let editId = null;
let currentData = [];
let farmList = [];
let batchList = [];
let herdList = [];
let barnList = [];

document.addEventListener('DOMContentLoaded', async () => {
    if (TOKEN && localStorage.getItem('user')) {
        CURRENT_USER = JSON.parse(localStorage.getItem('user'));
        await showMainPage();
    }
    document.getElementById('login-password').addEventListener('keypress', e => { if (e.key === 'Enter') login(); });
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', e => { e.preventDefault(); const page = item.dataset.page; if (page) loadPage(page); });
    });
    // 猪场切换时刷新批次列表
    const selFarm = document.getElementById('sel-farm');
    if (selFarm) selFarm.addEventListener('change', async () => {
        batchList = [];
        await loadBatchList();
        if (currentPage === 'herd') await onHerdFilter();
    });
}); // end DOMContentLoaded

async function login() {
    const u = document.getElementById('login-username').value.trim();
    const p = document.getElementById('login-password').value;
    if (!u || !p) return toast('请输入用户名和密码', 'error');
    try {
        const res = await fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username:u,password:p})});
        const json = await res.json();
        if (json.code !== 0) throw new Error(json.msg);
        TOKEN = json.data.token; CURRENT_USER = json.data;
        localStorage.setItem('token', TOKEN); localStorage.setItem('user', JSON.stringify(CURRENT_USER));
        await showMainPage(); toast('登录成功');
    } catch(e) { toast(e.message, 'error'); }
}

function logout() { TOKEN=''; CURRENT_USER=null; localStorage.removeItem('token'); localStorage.removeItem('user'); location.reload(); }

async function showMainPage() {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('main-page').style.display = 'block';
    document.getElementById('user-info').textContent = `${CURRENT_USER.name} (${CURRENT_USER.role})`;
    try { CONFIG = (await fetch('/api/config').then(r=>r.json())).data; } catch(e) {}
    await loadFarmList();
    await loadBatchList();
    loadPage('home');
}

async function loadFarmList() {
    try {
        farmList = (await request('/pig_farms')).data || [];
        const sel = document.getElementById('sel-farm');
        if (sel) {
            sel.innerHTML = '<option value="">全部猪场</option>';
            farmList.forEach(f => { sel.innerHTML += `<option value="${f.id}">${f.name}</option>`; });
        }
    } catch(e) {}
}

// 确保farmList已加载
async function ensureFarmList() {
    if (!farmList.length) await loadFarmList();
}

// 加载批次列表
async function loadBatchList() {
    try {
        // 加载全部批次（不受当前猪场筛选限制），确保新增批次立即可见
        batchList = (await request('/batches')).data || [];
    } catch(e) { batchList = []; }
}

// 确保batchList已加载
async function ensureBatchList() {
    if (!batchList.length) await loadBatchList();
}



// 批次选择 → 加载猪群+猪舍（免疫记录/免疫计划用）
function onBatchChangeForImmRec(batchSelId, herdSelId, barnSelId, farmSelId) {
    const batchId = document.getElementById(batchSelId)?.value;
    if (!batchId) return;
    const batch = batchList.find(b => String(b.id) === String(batchId));
    if (!batch) return;
    if (farmSelId) {
        const farmEl = document.getElementById(farmSelId);
        if (farmEl) farmEl.value = batch.farm_id || '';
    }
    const barnSel = document.getElementById(barnSelId);
    const herdSel = document.getElementById(herdSelId);
    if (barnSel) barnSel.innerHTML = '<option value="">加载中...</option>';
    if (herdSel) herdSel.innerHTML = '<option value="">加载中...</option>';
    (async () => {
        try {
            const barns = (await request(`/barns?farm_id=${batch.farm_id||''}`)).data||[];
            const herds = (await request(`/herds?farm_id=${batch.farm_id||''}`)).data||[];
            if (barnSel) barnSel.innerHTML = barns.length ? barns.map(b=>`<option value="${b.id}">${b.name}</option>`).join('') : '<option value="">无猪舍</option>';
            const filtered = herds.filter(h => String(h.batch_id) === String(batchId));
            if (herdSel) herdSel.innerHTML = filtered.length ? filtered.map(h=>`<option value="${h.id}">${h.herd_name||h.herd_code||''} (${h.pig_type||''},${h.quantity||0}头)</option>`).join('') : '<option value="">该批次暂无猪群</option>';
        } catch(e) {
            if (barnSel) barnSel.innerHTML = '<option value="">加载失败</option>';
            if (herdSel) herdSel.innerHTML = '<option value="">加载失败</option>';
        }
    })();
}
function toggleNav(el) { el.nextElementSibling.classList.toggle('show'); }

// ============ 页面切换 ============
async function loadPage(page) {
    currentPage = page;
    document.querySelectorAll('.nav-item').forEach(item => { item.classList.toggle('active', item.dataset.page === page); });
    document.querySelectorAll('.nav-items').forEach(items => items.classList.remove('show'));
    const activeNav = document.querySelector('.nav-item.active');
    if (activeNav) { const section = activeNav.closest('.nav-section'); if (section) section.querySelector('.nav-items').classList.add('show'); }
    
    const filterBar = document.getElementById('filter-bar');
    const monthW = document.getElementById('filter-month-wrapper');
    const noMonthPages = ['farm','barn','batch','herd','employee','breeding','farrowing','weaning','transfer','death','sales','immune-plan'];
    
    filterBar.style.display = (page==='home'||page==='params'||page==='profile') ? 'none' : 'flex';
    monthW.style.display = noMonthPages.includes(page) || page.startsWith('rpt-') ? 'none' : 'flex';
    
    if (!document.getElementById('sel-month').value) {
        const now = new Date();
        document.getElementById('sel-month').value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`;
    }
    
    const content = document.getElementById('page-content');
    
    const routes = {
        home: renderHome,
        farm: ()=>renderPage(page,'猪场信息',['code','name','address','manager','phone','stock_scale','built_date','area','status']),
        barn: ()=>renderPage(page,'猪舍管理',['farm_name','barn_code','name','barn_type','area','capacity','current_count','status','notes']),
        batch: ()=>renderPage(page,'批次管理',['batch_code','batch_name','farm_name','batch_type','start_date','expected_end_date','quantity','status','manager','notes']),
        herd: ()=>renderPage(page,'猪群管理',['batch_code','batch_name','farm_name','barn_name','herd_code','quantity','age_days','weight','in_date','status']),
        employee: ()=>renderPage(page,'员工管理',['farm_name','name','role','dept','phone','status']),
        breeding: ()=>renderPage(page,'配种记录',['batch_code','batch_name','sow_code','boar_code','breed_date','breed_method','expected_date','operator','status','notes']),
        farrowing: ()=>renderPage(page,'产仔记录',['batch_code','batch_name','sow_code','farrow_date','total_born','alive_born','healthy_count','dead_born','weak','mummy','avg_weight','litter_weight','notes']),
        weaning: ()=>renderPage(page,'断奶记录',['batch_code','batch_name','sow_code','wean_date','weaned_count','avg_weight','notes']),
        transfer: ()=>renderPage(page,'转舍记录',['batch_code','batch_name','herd_code','pig_type','barn_name','quantity','from_barn','to_barn','transfer_date','operator','notes']),
        death: ()=>renderPage(page,'死亡记录',['batch_code','batch_name','herd_code','pig_type','barn_name','quantity','death_type','reason','death_date','operator','notes']),
        sales: ()=>renderPage(page,'销售记录',['batch_code','batch_name','herd_code','pig_type','barn_name','quantity','total_weight','unit_price','total_amount','buyer','sale_date','operator','notes']),
        income: ()=>renderPage(page,'收入管理',['record_date','income_type','amount','month','description','operator','notes'],'month'),
        cost: ()=>renderPage(page,'成本管理',['record_date','cost_category','amount','month','description','operator','notes'],'month'),
        'immune-plan': ()=>renderPage(page,'免疫计划',['batch_code','batch_name','vaccine_name','immune_type','immune_age','immune_method','dosage','interval_days','status','notes'],''),
        'immune-record': ()=>renderPage(page,'免疫记录',['batch_code','batch_name','herd_code','herd_name','barn_name','pig_type','immune_date','vaccine_name','immune_type','quantity','immune_method','dosage','operator','notes'],'month'),
        'immune-reminder': renderImmuneReminder,
        'immune-report': renderImmuneReport,
        params: renderParams,
        profile: renderProfile,
        'rpt-inventory': ()=>renderStat('存栏统计','inventory',[{k:'pig_type',l:'猪只类型'},{k:'total',l:'存栏数量'}]),
        'rpt-farrowing': ()=>renderStat('产仔统计','farrowing',[{k:'farrow_count',l:'产仔窝数'},{k:'total_born',l:'总仔数'},{k:'alive_born',l:'活仔数'},{k:'avg_alive',l:'窝均活仔'}]),
        'rpt-weaning': ()=>renderStat('断奶统计','weaning',[{k:'wean_count',l:'断奶次数'},{k:'total_weaned',l:'断奶总数'},{k:'avg_weight',l:'均重(kg)'}]),
        'rpt-sales': ()=>renderStat('销售统计','sales',[{k:'pig_type',l:'类型'},{k:'total_qty',l:'数量'},{k:'total_amount',l:'金额'},{k:'avg_price',l:'单价'}],'total'),
        'rpt-death': ()=>renderStat('死亡统计','death',[{k:'death_type',l:'类型'},{k:'pig_type',l:'猪只类型'},{k:'total',l:'数量'}]),
        'rpt-income-expense': renderIncomeExpense,
        'rpt-cost': ()=>renderStat('成本汇总','cost_summary',[{k:'cost_category',l:'类型'},{k:'amount',l:'金额'}],'total',true),
        'rpt-perhead': renderPerHeadCost,
    };
    
    if (routes[page]) await routes[page]();
    else content.innerHTML = '<div class="empty-state">页面建设中...</div>';
}

async function doQuery() { await loadPage(currentPage); }

// ============ 个人中心 ============
async function renderProfile() {
    const content = document.getElementById('page-content');
    let userInfo = null;
    try {
        userInfo = (await request('/user/profile')).data;
    } catch(e) { toast(e.message, 'error'); return; }

    content.innerHTML = `
    <div class="page-header"><h2 class="page-title">个人中心</h2></div>
    <div style="max-width:560px;margin:0 auto">
        <div class="dashboard-card" style="margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:16px;padding:8px 0;border-bottom:1px solid #eee;margin-bottom:4px">
                <div style="width:52px;height:52px;border-radius:50%;background:linear-gradient(135deg,var(--primary),var(--accent));display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700;color:#fff;flex-shrink:0">
                    ${(userInfo.name||'U')[0]}
                </div>
                <div>
                    <div style="font-size:17px;font-weight:600;color:var(--gray-900)">${userInfo.name||''}</div>
                    <div style="font-size:13px;color:var(--gray-500);margin-top:3px">
                        <span style="display:inline-block;background:rgba(27,111,248,0.1);color:var(--primary);padding:2px 8px;border-radius:10px;font-size:12px;font-weight:500">${userInfo.role||''}</span>
                    </div>
                </div>
            </div>
            <div style="font-size:12px;color:var(--gray-400);padding-top:4px">登录账号：${userInfo.username||''}</div>
        </div>

        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;color:var(--gray-800);margin-bottom:20px;padding-bottom:10px;border-bottom:1px solid #eee">修改密码与账号</h3>
            <div class="form-row">
                <div class="form-group">
                    <label>登录账号</label>
                    <input class="form-input" type="text" id="p-username" value="${userInfo.username||''}" placeholder="请输入登录账号" style="width:100%;padding:9px 12px;border:1.5px solid var(--gray-200);border-radius:8px;font-size:14px;outline:none;box-sizing:border-box">
                </div>
            </div>
            <div class="form-group">
                <label>原密码 <span style="color:red">*</span></label>
                <input class="form-input" type="password" id="p-old-pwd" placeholder="请输入原密码" style="width:100%;padding:9px 12px;border:1.5px solid var(--gray-200);border-radius:8px;font-size:14px;outline:none;box-sizing:border-box">
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>新密码 <span style="color:red">*</span></label>
                    <input class="form-input" type="password" id="p-new-pwd" placeholder="至少6位" style="width:100%;padding:9px 12px;border:1.5px solid var(--gray-200);border-radius:8px;font-size:14px;outline:none;box-sizing:border-box">
                </div>
                <div class="form-group">
                    <label>确认新密码 <span style="color:red">*</span></label>
                    <input class="form-input" type="password" id="p-confirm-pwd" placeholder="再次输入新密码" style="width:100%;padding:9px 12px;border:1.5px solid var(--gray-200);border-radius:8px;font-size:14px;outline:none;box-sizing:border-box">
                </div>
            </div>
            <div style="margin-top:24px">
                <button class="btn btn-primary" onclick="submitProfileChange()" style="min-width:120px">保存修改</button>
            </div>
            <div id="pwd-tip" style="font-size:12px;color:var(--gray-400);margin-top:10px">不修改账号时，可只填写原密码和新密码</div>
        </div>
    </div>`;

    content.querySelectorAll('.form-input').forEach(inp => {
        inp.addEventListener('focus', () => { inp.style.borderColor = 'var(--primary)'; });
        inp.addEventListener('blur', () => { inp.style.borderColor = 'var(--gray-200)'; });
    });
}

async function submitProfileChange() {
    const username = document.getElementById('p-username').value.trim();
    const oldPwd = document.getElementById('p-old-pwd').value;
    const newPwd = document.getElementById('p-new-pwd').value;
    const confirmPwd = document.getElementById('p-confirm-pwd').value;
    if (!oldPwd) { toast('请输入原密码', 'error'); return; }
    if (!newPwd) { toast('请输入新密码', 'error'); return; }
    if (newPwd.length < 6) { toast('新密码长度不能少于6位', 'error'); return; }
    if (newPwd !== confirmPwd) { toast('新密码与确认密码不一致', 'error'); return; }
    try {
        const res = await request('/user/change-password', {
            method: 'POST',
            body: JSON.stringify({ username, old_password: oldPwd, new_password: newPwd, confirm_password: confirmPwd })
        });
        if (res.code !== 0) throw new Error(res.msg);
        toast('修改成功，请使用新账号重新登录', 'success');
        setTimeout(() => { logout(); }, 1800);
    } catch(e) { toast(e.message, 'error'); }
}

// ============ 通用列表页 ============
async function renderPage(page, title, cols, filterBy) {
    filterBy = filterBy || '';
    const farmId = document.getElementById('sel-farm').value;
    const month = document.getElementById('sel-month').value;
    const content = document.getElementById('page-content');

    const headers = getColHeaders(page);
    const exportPages = ['farm','barn','batch','herd','employee','breeding','farrowing','weaning','transfer','death','sales','income','cost','immune-plan','immune-record'];

    // 猪群页面：附加批次 + 状态双筛选器
    const herdFilters = page === 'herd' ? `
        <div class="filter-item">
            <label>批次</label>
            <select id="sel-herd-batch" onchange="onHerdFilter()">
                <option value="">全部批次</option>
                ${batchList.map(b=>`<option value="${b.id}">${b.batch_code} ${b.batch_name||''}</option>`).join('')}
            </select>
        </div>
        <div class="filter-item">
            <label>状态</label>
            <select id="sel-herd-status" onchange="onHerdFilter()">
                <option value="">全部</option>
                <option value="存栏">存栏</option>
                <option value="已断奶">已断奶</option>
                <option value="已转舍">已转舍</option>
                <option value="已销售">已销售</option>
                <option value="已死亡">已死亡</option>
                <option value="已淘汰">已淘汰</option>
                <option value="已清群">已清群</option>
                <option value="免疫中">免疫中</option>
            </select>
        </div>` : '';

    content.innerHTML = `<div class="page-header"><h2 class="page-title">${title}</h2></div>
        <div class="filter-bar">
            ${herdFilters}
            <div class="filter-actions">
                <button class="btn btn-primary btn-sm" onclick="openAddModal()">+ 新增</button>
                <button class="btn btn-outline btn-sm" onclick="exportCurrentList()">导出</button>
                ${exportPages.includes(page) ? `<button class="btn btn-outline btn-sm" onclick="openImportModal()">批量导入</button>` : ''}
            </div>
        </div>
        <div class="table-box"><table><thead><tr>${cols.map((c,i)=>`<th>${headers[c]||headers[i]||c}</th>`).join('')}<th>操作</th></tr></thead>
        <tbody id="table-body"><tr><td colspan="${cols.length+1}" class="empty-state">加载中...</td></tr></tbody></table></div>`;

    try {
        let data = await loadPageData(page, farmId, month);
        // 猪群页面：批次+状态前端筛选
        if (page === 'herd') {
            const batchVal = document.getElementById('sel-herd-batch')?.value || '';
            const statusVal = document.getElementById('sel-herd-status')?.value || '';
            if (batchVal) data = data.filter(r => String(r.batch_id) === batchVal);
            if (statusVal) data = data.filter(r => r.status === statusVal);
        }
        currentData = data;
        renderTableData(cols, data, headers, page === 'herd' ? {herdPage: true} : {});
    } catch(e) { document.getElementById('table-body').innerHTML = `<tr><td colspan="${cols.length+1}" class="empty-state">${e.message}</td></tr>`; }
}

// 猪群页面：批次+状态 联动筛选
async function onHerdFilter() {
    const farmId = document.getElementById('sel-farm').value;
    const batchVal = document.getElementById('sel-herd-batch')?.value || '';
    const statusVal = document.getElementById('sel-herd-status')?.value || '';
    let data = await loadPageData('herd', farmId, '');
    if (batchVal) data = data.filter(r => String(r.batch_id) === batchVal);
    if (statusVal) data = data.filter(r => r.status === statusVal);
    currentData = data;
    const herdCols = ['batch_code','batch_name','farm_name','barn_name','herd_code','quantity','age_days','weight','in_date','status'];
    renderTableData(herdCols, data, getColHeaders('herd'), {herdPage: true});
}

function getColHeaders(page) {
    const H = {
        farm: ['编码','名称','地址','负责人','电话','存栏规模','建成时间','面积(亩)','状态'],
        barn: ['所属猪场','猪舍编号','名称','类型','面积','容量','当前存栏','状态','备注'],
        batch: ['批次编号','批次名称','所属猪场','批次类型','开始日期','预计结束','头数','状态','负责人','备注'],
        herd: ['批次编号','批次名称','猪场','猪舍','猪群编号','数量','日龄','存栏重量(kg)','入群日期','状态'],
        employee: ['猪场','姓名','职位','部门','电话','状态'],
        breeding: ['批次编号','批次名称','母猪号','公猪号','配种日期','方式','预产日期','操作人','状态','备注'],
        farrowing: ['批次编号','批次名称','母猪号','产仔日期','总仔','活仔','健仔','死胎','弱仔','木乃伊','均重(kg)','窝重(kg)','备注'],
        weaning: ['批次编号','批次名称','母猪号','断奶日期','断奶头数','均重(kg)','备注'],
        transfer: ['批次编号','批次名称','耳号','猪只类型','猪舍','数量','转出','转入','日期','操作人','备注'],
        death: ['批次编号','批次名称','耳号','猪只类型','猪舍','数量','类型','原因','日期','操作人','备注'],
        sales: ['批次编号','批次名称','耳号','猪只类型','猪舍','数量','总重量','单价','总金额','买家','日期','操作人','备注'],
        income: ['日期','类型','金额','月份','描述','操作人','备注'],
        cost: ['日期','类型','金额','月份','描述','操作人','备注'],
        'immune-plan': ['批次编号','批次名称','疫苗名称','免疫类型','应免日龄','免疫方式','剂量','间隔天数','状态','备注'],
        'immune-record': ['批次编号','批次名称','猪群编号','猪群名称','猪舍','猪只类型','免疫日期','疫苗名称','免疫类型','数量','免疫方式','剂量','操作人','备注'],
    };
    return H[page] || [];
}

function getPageApi(page) {
    const M = {
        farm:'/pig_farms', barn:'/barns', batch:'/batches', herd:'/herds', employee:'/employees',
        breeding:'/breeding_records', farrowing:'/farrowing_records', weaning:'/weaning_records',
        transfer:'/transfer_records', death:'/death_records', sales:'/sales_records',
        income:'/income_records', cost:'/cost_records',
        'immune-plan':'/immune_plans/all', 'immune-record':'/immune_records',
    };
    return M[page] || '';
}

async function loadPageData(page, farmId, month) {
    const api = getPageApi(page);
    if (!api) return [];
    let url = `${api}?farm_id=${farmId||''}`;
    if (month && ['income','cost','immune-record'].includes(page)) url += `&month=${month}`;
    return (await request(url)).data || [];
}

function renderTableData(cols, data, headers, extraOpts) {
    const tb = document.getElementById('table-body');
    if (!data.length) { tb.innerHTML = `<tr><td colspan="${cols.length+1}" class="empty-state">暂无数据</td></tr>`; return; }

    // farm_name特殊处理
    let dispData = data.map(row => {
        let r = {...row};
        if ('farm_id' in r && typeof r.farm_id === 'number') {
            const farm = farmList.find(f => f.id === r.farm_id);
            r._farm_name = farm ? farm.name : r.farm_id;
        }
        return r;
    });

    // 状态标签颜色映射（支持猪群页面）
    function getStatusBadge(v, isHerd) {
        if (!isHerd) {
            const cls = v==='正常'||v==='启用'||v==='在群'||v==='在职' ? 'badge-green' : 'badge-red';
            return `<span class="badge ${cls}">${v||''}</span>`;
        }
        // 猪群专用状态颜色
        const map = {
            '存栏':   'badge-green',
            '已断奶': 'badge-blue',
            '已转舍': 'badge-primary',
            '已销售': 'badge-blue',
            '已死亡': 'badge-red',
            '已淘汰': 'badge-orange',
            '已清群': 'badge-gray',
            '免疫中': 'badge-yellow',
            '在群':   'badge-green',
        };
        const cls = map[v] || 'badge-gray';
        return `<span class="badge ${cls}">${v||'存栏'}</span>`;
    }

    const isHerdPage = extraOpts && extraOpts.herdPage;
    tb.innerHTML = dispData.map(row => `<tr>
        ${cols.map((c,ci) => {
            let v = c === 'farm_id' ? (row._farm_name || row.farm_id) : (row[c] ?? row[ci]);
            if (c==='amount'||c==='total_amount'||c==='avg_weight'||c==='unit_price'||c==='area'||c==='stock_scale') v = n(v);
            if (c==='weight' && (v || row.weight)) v = n(v);
            if (c==='status') {
                v = getStatusBadge(v, isHerdPage);
            }
            return `<td>${v!==null&&v!==undefined?String(v):'-'}</td>`;
        }).join('')}
        <td class="table-actions">
            <button class="btn btn-outline btn-sm" onclick="editRecord(${row.id})">编辑</button>
            <button class="btn btn-danger btn-sm" onclick="delRecord(${row.id})">删除</button>
        </td>
    </tr>`).join('');
}

// ============ 首页 ============
async function renderHome() {
    const farmId = document.getElementById('sel-farm').value;
    const content = document.getElementById('page-content');
    
    let data;
    try {
        data = (await request(`/dashboard${farmId? '?farm_id='+farmId:''}`)).data;
    } catch(e) {
        content.innerHTML = '<div class="empty-state">加载数据失败</div>';
        return;
    }
    
    const s = data.summary;
    const fmt = n => (n||0).toLocaleString();
    
    let html = `
    <div class="page-header" style="margin-bottom:20px">
        <h2 class="page-title">数据看板</h2>
        <div style="font-size:13px;color:var(--gray-500)">${new Date().toLocaleDateString('zh-CN',{year:'numeric',month:'long',day:'numeric',weekday:'long'})}</div>
    </div>
    
    <!-- 顶部数字卡片 -->
    <div class="stats-grid" style="margin-bottom:20px">
        <div class="stat-card" style="border-left-color:#1b6ff8">
            <div class="stat-label">总存栏</div>
            <div class="stat-value">${fmt(s.total_inventory)}<span class="stat-unit">头</span></div>
            <div style="font-size:11px;color:var(--gray-400);margin-top:4px">今日新增 +${s.today_new}</div>
        </div>
        <div class="stat-card" style="border-left-color:#10b981">
            <div class="stat-label">今日销售</div>
            <div class="stat-value">${fmt(s.today_sales_qty)}<span class="stat-unit">头</span></div>
            <div style="font-size:11px;color:var(--gray-400);margin-top:4px">金额 ¥${fmt(s.today_sales_amt)}</div>
        </div>
        <div class="stat-card" style="border-left-color:#ef4444">
            <div class="stat-label">今日死亡/淘汰</div>
            <div class="stat-value">${fmt(s.today_death)}<span class="stat-unit">头</span></div>
        </div>
        <div class="stat-card" style="border-left-color:#8b5cf6">
            <div class="stat-label">本月收入</div>
            <div class="stat-value">¥${fmt(data.monthly_income)}</div>
            <div style="font-size:11px;color:var(--gray-400);margin-top:4px">成本 ¥${fmt(data.monthly_cost_total)}</div>
        </div>
        <div class="stat-card" style="border-left-color:#f59e0b">
            <div class="stat-label">猪场 / 猪舍 / 批次</div>
            <div class="stat-value">${s.farm_count} / ${s.barn_count} / ${s.batch_count}</div>
        </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="dashboard-grid" style="margin-bottom:20px">
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">存栏类型分布</h3>
            <div style="height:220px"><canvas id="chart-inventory-type"></canvas></div>
        </div>
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">猪舍存栏统计</h3>
            <div style="height:220px"><canvas id="chart-barn-inventory"></canvas></div>
        </div>
    </div>
    
    <!-- 批次 + 免疫提醒 + 最近记录 -->
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:20px" class="dash-3col">
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">批次概览</h3>
            <div style="max-height:260px;overflow-y:auto">
                <table class="dash-table">
                    <thead><tr><th>批次</th><th>数量</th><th>状态</th></tr></thead>
                    <tbody>
                        ${data.batch_summary.slice(0,8).map(b=>`
                            <tr>
                                <td title="${b.batch_name||''}">${(b.batch_code||'').slice(0,12)}</td>
                                <td>${b.current_qty||0}/${b.quantity||0}</td>
                                <td>${b.status?'<span class="badge badge-'+(b.status==='进行中'?'blue':b.status==='已完成'?'green':'gray')+'">'+b.status+'</span>':'-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">待免疫提醒</h3>
            <div style="max-height:260px;overflow-y:auto">
                ${data.immune_reminders.length===0?'<div class="empty-state" style="padding:40px 0">暂无待免疫</div>':`
                    <table class="dash-table">
                        <thead><tr><th>疫苗</th><th>批次</th><th>日期</th></tr></thead>
                        <tbody>
                            ${data.immune_reminders.slice(0,8).map(r=>`
                                <tr>
                                    <td>${r.vaccine_name||'-'}</td>
                                    <td>${r.batch_code||'-'}</td>
                                    <td style="color:${r.is_overdue?'#ef4444':'inherit'}">${r.reminder_date||'-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `}
            </div>
        </div>
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">最近生产记录</h3>
            <div style="max-height:260px;overflow-y:auto">
                ${data.recent_records.length===0?'<div class="empty-state" style="padding:40px 0">暂无记录</div>':`
                    <table class="dash-table">
                        <thead><tr><th>类型</th><th>数量</th><th>日期</th></tr></thead>
                        <tbody>
                            ${data.recent_records.map(r=>`
                                <tr>
                                    <td><span class="badge badge-${r.type==='sale'?'green':'red'}">${r.type==='sale'?'销售':'死亡'}</span></td>
                                    <td>${r.quantity||0}</td>
                                    <td>${r.record_date||'-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `}
            </div>
        </div>
    </div>
    
    <!-- 快捷入口 -->
    <div class="dashboard-grid">
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">快捷功能</h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
                <button class="btn btn-outline" onclick="loadPage('herd')">猪群管理</button>
                <button class="btn btn-outline" onclick="loadPage('batch')">批次管理</button>
                <button class="btn btn-outline" onclick="loadPage('immune-reminder')">免疫提醒</button>
                <button class="btn btn-outline" onclick="loadPage('immune-record')">免疫记录</button>
            </div>
        </div>
        <div class="dashboard-card">
            <h3 style="font-size:14px;font-weight:600;margin-bottom:12px">快速录入</h3>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
                <button class="btn btn-outline" onclick="openAddModal()">新增记录</button>
                <button class="btn btn-outline" onclick="openImportModal()">批量导入</button>
                <button class="btn btn-outline" onclick="exportCurrentList()">导出列表</button>
                <button class="btn btn-outline" onclick="loadPage('params')">参数设置</button>
            </div>
        </div>
    </div>`;
    
    content.innerHTML = html;
    
    // 绑定图表
    setTimeout(() => {
        // 饼图：存栏类型分布
        const pieData = data.inventory_by_type;
        if (pieData && pieData.length > 0) {
            const ctx1 = document.getElementById('chart-inventory-type');
            if (ctx1) {
                new Chart(ctx1, {
                    type: 'doughnut',
                    data: {
                        labels: pieData.map(d => d.pig_type || '未分类'),
                        datasets: [{
                            data: pieData.map(d => d.total || 0),
                            backgroundColor: ['#1b6ff8','#10b981','#f59e0b','#8b5cf6','#ef4444','#6b7280'],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 15 } } }
                    }
                });
            }
        }
        
        // 柱状图：猪舍存栏
        const barData = data.barn_inventory;
        if (barData && barData.length > 0) {
            const ctx2 = document.getElementById('chart-barn-inventory');
            if (ctx2) {
                new Chart(ctx2, {
                    type: 'bar',
                    data: {
                        labels: barData.map(d => d.barn_name || '未命名'),
                        datasets: [{
                            label: '存栏数量',
                            data: barData.map(d => d.total || 0),
                            backgroundColor: '#1b6ff8',
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true, ticks: { stepSize: 50 } } }
                    }
                });
            }
        }
    }, 100);
}

// ============ 免疫 ============
async function renderImmuneReminder() {
    const farmId = document.getElementById('sel-farm').value;
    const content = document.getElementById('page-content');
    content.innerHTML = `<div class="page-header"><h2 class="page-title">免疫提醒</h2><div style="margin-top:4px;font-size:12px;color:#6b7280">根据猪群日龄和免疫计划自动计算</div></div>
        <div class="stats-grid" id="reminder-stats"></div>
        <div class="table-box"><table><thead><tr><th>紧急程度</th><th>猪群</th><th>猪只类型</th><th>当前日龄</th><th>疫苗名称</th><th>免疫类型</th><th>应免日龄</th><th>免疫方式</th><th>剂量</th><th>操作</th></tr></thead><tbody id="table-body"><tr><td colspan="10" class="empty-state">加载中...</td></tr></tbody></table></div>`;

    try {
        const data = (await request(`/immune_reminders?farm_id=${farmId||''}`)).data||[];
        const overdue = data.filter(r=>r.is_overdue).length;
        const soon = data.filter(r=>!r.is_overdue&&r.days_until!==null&&r.days_until<=7).length;
        document.getElementById('reminder-stats').innerHTML = `
            <div class="stat-card red"><div class="stat-label">已过期</div><div class="stat-value">${overdue}</div><div class="stat-sub">需立即处理</div></div>
            <div class="stat-card yellow"><div class="stat-label">7天内到期</div><div class="stat-value">${soon}</div><div class="stat-sub">请及时安排</div></div>
            <div class="stat-card green"><div class="stat-label">待免疫总数</div><div class="stat-value">${data.length}</div><div class="stat-sub">全部待免记录</div></div>`;

        document.getElementById('table-body').innerHTML = data.length ? data.map(row => {
            const urgency = row.is_overdue?'已过期':(row.days_until===0?'今日到期':(row.days_until!==null?`${row.days_until}天后`:'待首免'));
            const cls = row.is_overdue?'badge-red':(row.days_until===0?'badge-orange':(row.days_until!==null&&row.days_until<=3?'badge-yellow':'badge-gray'));
            return `<tr>
                <td><span class="badge ${cls}">${urgency}</span></td>
                <td><strong>${row.herd_name||''}</strong>${row.herd_code?`<br><span class="text-sm text-muted">${row.herd_code}</span>`:''}</td>
                <td>${row.pig_type||''}</td>
                <td><span class="fw-600">${row.current_age||0}</span> 日龄</td>
                <td><strong style="color:var(--primary)">${row.vaccine_name||''}</strong></td>
                <td>${row.immune_type||''}</td>
                <td>${row.immune_age||0} 日龄</td>
                <td>${row.immune_method||''}</td>
                <td>${row.dosage||''}</td>
                <td><button class="btn btn-success btn-sm" onclick="quickImmune(${row.herd_id},'${row.vaccine_name||''}','${row.immune_type||''}',${row.current_age||0})">快速登记</button></td>
            </tr>`;
        }).join('') : '<tr><td colspan="10" class="empty-state">暂无待免疫提醒，当前无免疫任务</td></tr>';
        currentData = data;
    } catch(e) { document.getElementById('table-body').innerHTML = `<tr><td colspan="10" class="empty-state">${e.message}</td></tr>`; }
}

async function quickImmune(herdId, vaccine, type, age) {
    await ensureFarmList();
    const farmId = parseInt(document.getElementById('sel-farm').value)||1;
    const now = new Date().toISOString().slice(0,10);
    editId = null; currentPage = 'immune-record';
    document.getElementById('modal-title').textContent = '快速登记免疫';
    document.getElementById('modal-body').innerHTML = await buildFormHtml('immune-record', {herd_id:herdId,vaccine_name:vaccine,immune_type:type,immune_age:age,immune_date:now,farm_id:farmId});
    document.getElementById('modal-save-btn').textContent = '确定 / 保存';
    document.getElementById('modal').classList.add('show');
}

async function renderImmuneReport() {
    const farmId = document.getElementById('sel-farm').value;
    const month = document.getElementById('sel-month').value;
    const content = document.getElementById('page-content');
    content.innerHTML = `<div class="page-header"><h2 class="page-title">免疫报表</h2></div>
        <div class="dashboard-grid">
            <div class="dashboard-card"><h3>免疫统计</h3><div class="table-box" style="overflow:auto"><table id="is"><thead><tr><th>疫苗</th><th>类型</th><th>免疫数量</th><th>记录次数</th></tr></thead><tbody><tr><td colspan="4" class="empty-state">加载中...</td></tr></tbody></table></div></div>
            <div class="dashboard-card"><h3>未免疫(已过期)</h3><div class="table-box" style="overflow:auto"><table id="uf"><thead><tr><th>猪群</th><th>类型</th><th>当前日龄</th><th>疫苗</th><th>过期天数</th></tr></thead><tbody><tr><td colspan="5" class="empty-state">加载中...</td></tr></tbody></table></div></div>
        </div>`;
    try {
        const sum = (await request(`/reports/immune_summary?farm_id=${farmId||''}&month=${month||''}`)).data;
        document.getElementById('is').querySelector('tbody').innerHTML = sum.data?.length ? sum.data.map(r=>`<tr><td>${r.vaccine_name||''}</td><td>${r.immune_type||''}</td><td>${r.total_qty||0}</td><td>${r.record_count||0}</td></tr>`).join('') : '<tr><td colspan="4" class="empty-state">暂无数据</td></tr>';
        const uf = (await request(`/reports/immune_unfinished?farm_id=${farmId||''}`)).data;
        document.getElementById('uf').querySelector('tbody').innerHTML = uf.data?.length ? uf.data.map(r=>`<tr style="background:#fff0f0"><td>${r.herd_name||''}</td><td>${r.pig_type||''}</td><td>${r.current_age||0}日龄</td><td><strong>${r.vaccine_name||''}</strong></td><td style="color:#dc3545">${r.days_until||0}天</td></tr>`).join('') : '<tr><td colspan="5" class="empty-state">暂无已过期</td></tr>';
    } catch(e) {}
}

// ============ 报表 ============
async function renderStat(title, api, cols, sumKey, isCost) {
    const farmId = document.getElementById('sel-farm').value;
    const month = document.getElementById('sel-month').value;
    const content = document.getElementById('page-content');
    content.innerHTML = `<div class="page-header"><h2 class="page-title">${title}</h2></div>
        <div class="stats-grid"><div class="stat-card ${isCost?'red':'green'}"><div class="stat-label">${title}</div><div class="stat-value" id="tv">-</div></div></div>
        <div class="table-box"><table id="rt"><thead><tr>${cols.map(c=>`<th>${c.l}</th>`).join('')}</tr></thead><tbody id="rb"><tr><td colspan="${cols.length}" class="empty-state">加载中...</td></tr></tbody></table></div>`;
    try {
        const data = (await request(`/reports/${api}?farm_id=${farmId||''}&month=${month||''}`)).data;
        const rows = Array.isArray(data) ? data : (data?.data || []);
        const total = data?.total !== undefined ? data.total : (Array.isArray(data) ? null : 0);
        if (sumKey && total !== null) document.getElementById('tv').textContent = fm(total);
        else if (!Array.isArray(data)) { const v = Object.values(data||{}).filter(x=>typeof x==='number').reduce((a,b)=>a+b,0); document.getElementById('tv').textContent = fm(v); }
        document.getElementById('rb').innerHTML = rows.length ? rows.map(row => `<tr>${cols.map(c=>`<td ${isCost&&c.k==='amount'?'style="color:var(--red)"':''}>${fm(row[c.k]??'')}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${cols.length}" class="empty-state">暂无数据</td></tr>`;
    } catch(e) { document.getElementById('rb').innerHTML = `<tr><td colspan="${cols.length}" class="empty-state">${e.message}</td></tr>`; }
}

async function renderIncomeExpense() {
    const farmId = document.getElementById('sel-farm').value;
    const month = document.getElementById('sel-month').value;
    const content = document.getElementById('page-content');
    content.innerHTML = `<div class="page-header"><h2 class="page-title">月度收支表</h2></div>
        <div class="stats-grid">
            <div class="stat-card green"><div class="stat-label">收入合计</div><div class="stat-value" id="it">-</div></div>
            <div class="stat-card red"><div class="stat-label">成本合计</div><div class="stat-value" id="ct">-</div></div>
            <div class="stat-card"><div class="stat-label">盈亏</div><div class="stat-value" id="pv">-</div></div>
        </div>
        <div class="dashboard-grid">
            <div class="dashboard-card"><h3>收入明细</h3><table><thead><tr><th>类型</th><th>金额</th></tr></thead><tbody id="ib"><tr><td colspan="2" class="empty-state">-</td></tr></tbody></table></div>
            <div class="dashboard-card"><h3>成本明细</h3><table><thead><tr><th>类型</th><th>金额</th></tr></thead><tbody id="cb"><tr><td colspan="2" class="empty-state">-</td></tr></tbody></table></div>
        </div>`;
    try {
        const d = (await request(`/reports/monthly_income_expense?farm_id=${farmId||''}&month=${month||''}`)).data;
        document.getElementById('it').textContent = fm(d.total_income||0);
        document.getElementById('ct').textContent = fm(d.total_cost||0);
        const profit = d.profit||0;
        document.getElementById('pv').innerHTML = `<span style="color:${profit>=0?'var(--green)':'var(--red)'}">${fm(profit)}</span>`;
        document.getElementById('ib').innerHTML = d.income?.length ? d.income.map(r=>`<tr><td>${r.income_type||''}</td><td class="text-right" style="color:var(--green)">${fm(r.amount||0)}</td></tr>`).join('') : '<tr><td colspan="2" class="empty-state">暂无</td></tr>';
        document.getElementById('cb').innerHTML = d.cost?.length ? d.cost.map(r=>`<tr><td>${r.cost_category||''}</td><td class="text-right" style="color:var(--red)">${fm(r.amount||0)}</td></tr>`).join('') : '<tr><td colspan="2" class="empty-state">暂无</td></tr>';
    } catch(e) {}
}

async function renderPerHeadCost() {
    const farmId = document.getElementById('sel-farm').value;
    const month = document.getElementById('sel-month').value;
    const content = document.getElementById('page-content');
    content.innerHTML = `<div class="page-header"><h2 class="page-title">头均成本</h2></div>
        <div class="stats-grid">
            <div class="stat-card red"><div class="stat-label">总成本</div><div class="stat-value" id="tc">-</div></div>
            <div class="stat-card"><div class="stat-label">销售头数</div><div class="stat-value" id="sh">-</div></div>
            <div class="stat-card"><div class="stat-label">存栏头数</div><div class="stat-value" id="iv">-</div></div>
            <div class="stat-card green"><div class="stat-label">头均成本</div><div class="stat-value" id="ph">-</div></div>
        </div>`;
    try {
        const d = (await request(`/reports/per_head_cost?farm_id=${farmId||''}&month=${month||''}`)).data;
        document.getElementById('tc').textContent = fm(d.total_cost||0);
        document.getElementById('sh').textContent = `${d.sales_heads||0} 头`;
        document.getElementById('iv').textContent = `${d.inventory||0} 头`;
        document.getElementById('ph').innerHTML = `${fm(d.per_head_cost||0)} <span class="stat-unit">元/头</span>`;
    } catch(e) {}
}

// ============ 参数设置 ============
async function renderParams() {
    const content = document.getElementById('page-content');
    content.innerHTML = `<div class="page-header"><h2 class="page-title">系统参数设置</h2></div>
        <div class="filter-actions" style="margin-bottom:12px">
            <button class="btn btn-outline" onclick="resetParams()">重置为默认</button>
            <button class="btn btn-primary" onclick="saveAllParams()">保存全部</button>
        </div>
        <div id="params-container">加载中...</div>`;
    try {
        const data = (await request('/system_params')).data||[];
        const cats = {general:'通用设置',production:'生产参数',finance:'财务参数'};
        const catDesc = {general:'系统通用配置项',production:'猪场生产相关参数',finance:'财务单价默认值'};
        let html = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px">';
        for (const [cat,catName] of Object.entries(cats)) {
            const items = data.filter(p=>p.category===cat);
            if (!items.length) continue;
            html += `<div class="dashboard-card"><h3>${catName}</h3><p style="font-size:12px;color:#888;margin-bottom:12px">${catDesc[cat]||''}</p>
                ${items.map(p=>`<div style="display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #eee">
                    <div style="flex:1"><div style="font-weight:500">${p.param_name}</div><div style="font-size:11px;color:#999">${p.description||''}</div></div>
                    ${p.param_type==='select'?
                        `<select class="param-input" data-id="${p.id}" style="padding:4px 8px;border:1px solid #ddd;border-radius:4px;min-width:100px">${
                            (p.options||'').split(',').map(o=>`<option value="${o}" ${p.param_value===o?'selected':''}>${o}</option>`).join('')
                        }</select>`:
                        `<input class="param-input" data-id="${p.id}" type="${p.param_type==='number'?'number':'text'}" value="${p.param_value||''}" style="padding:4px 8px;border:1px solid #ddd;border-radius:4px;width:120px">`
                    }
                </div>`).join('')}
            </div>`;
        }
        html += '</div>';
        document.getElementById('params-container').innerHTML = html;
    } catch(e) { document.getElementById('params-container').innerHTML = `<div class="empty-state">${e.message}</div>`; }
}

async function saveAllParams() {
    const items = Array.from(document.querySelectorAll('.param-input')).map(el=>({id:parseInt(el.dataset.id),param_value:el.value}));
    try { await request('/system_params/batch',{method:'POST',body:JSON.stringify({items})}); toast('保存成功'); } catch(e) { toast(e.message,'error'); }
}

async function resetParams() {
    if (!confirm('确定要重置所有参数为默认值吗？')) return;
    try { await request('/system_params/reset',{method:'POST'}); toast('已重置'); await renderParams(); } catch(e) { toast(e.message,'error'); }
}

// ============ 弹窗表单 ============
async function openAddModal() {
    await ensureFarmList();
    await ensureBatchList();
    editId = null;

    // 免疫提醒页 → 实际打开免疫记录表单
    const _page = currentPage === 'immune-reminder' ? 'immune-record' : currentPage;
    document.getElementById('modal-title').textContent = '新增 ' + getPageTitle(_page);
    document.getElementById('modal-body').innerHTML = await buildFormHtml(_page, {});
    document.getElementById('modal-save-btn').textContent = '确定 / 保存';
    document.getElementById('modal').classList.add('show');
}

async function editRecord(id) {
    await ensureFarmList();
    await ensureBatchList();
    editId = id;
    const row = currentData.find(r=>r.id===id);
    if (!row) return;
    document.getElementById('modal-title').textContent = '编辑 ' + getPageTitle(currentPage);
    document.getElementById('modal-body').innerHTML = await buildFormHtml(currentPage, row);
    document.getElementById('modal-save-btn').textContent = '确定 / 保存';
    document.getElementById('modal').classList.add('show');
}

function getPageTitle(p) {
    const t = {farm:'猪场信息',barn:'猪舍管理',batch:'批次管理',herd:'猪群管理',employee:'员工',breeding:'配种记录',farrowing:'产仔记录',weaning:'断奶记录',transfer:'转舍记录',death:'死亡记录',sales:'销售记录',income:'收入',cost:'成本','immune-plan':'免疫计划','immune-record':'免疫记录'};
    return t[p]||p;
}

async function saveData() {
    // 导入模式：切换到导入逻辑
    if (_importMode) { await doImport(); return; }

    const form = document.getElementById('modal-body');

    // 收集表单数据
    const data = {};
    form.querySelectorAll('input,select,textarea').forEach(el=>{
        if (el.name) data[el.name] = el.type==='number' ? +(el.value||0) : el.value;
    });

    // 必填项校验
    const reqFields = {
        farm:['code','name'], barn:['farm_id','name'], batch:['batch_name','farm_id','batch_type','start_date'],
        herd:['batch_id'],
        breeding:['sow_code','breed_date'], farrowing:['sow_code','farrow_date'],
        weaning:['wean_date'], transfer:['transfer_date'], death:['death_date'],
        sales:['pig_type','quantity','sale_date'], income:['income_type','amount','month'],
        cost:['cost_category','amount','month'],
        'immune-plan':['vaccine_name'], 'immune-record':['immune_date','vaccine_name']
    };
    const required = reqFields[currentPage] || [];
    for (const f of required) {
        const el = form.querySelector(`[name="${f}"]`);
        if (!data[f] || String(data[f]).trim() === '') {
            toast(`请填写必填项：${f}`, 'error');
            if (el) el.focus();
            return;
        }
    }

    if (!data.farm_id && currentPage !== 'farm') {
        data.farm_id = parseInt(document.getElementById('sel-farm').value) || 1;
    }

    const api = getPageApi(currentPage);
    if (!api) return;
    try {
        if (editId) await request(`${api}/${editId}`,{method:'PUT',body:JSON.stringify(data)});
        else await request(api,{method:'POST',body:JSON.stringify(data)});
        toast('保存成功！'); closeModal(); await loadPage(currentPage);
    } catch(e) { toast(e.message, 'error'); }
}

async function delRecord(id) {
    if (!confirm('确定要删除吗？')) return;
    const api = getPageApi(currentPage);
    if (!api) return;
    try { await request(`${api}/${id}`,{method:'DELETE'}); toast('删除成功'); await loadPage(currentPage); } catch(e) { toast(e.message,'error'); }
}

function closeModal() { document.getElementById('modal').classList.remove('show'); editId=null; _importMode=false; }

function onCancelClick() {
    // 取消：确认后返回
    if (_importMode) { closeModal(); return; }
    const discard = confirm('是否放弃本次编辑？');
    if (discard) closeModal();
}

// ============ 构建表单HTML ============
async function buildFormHtml(page, row) {
    const cfg = CONFIG || {};
    const now = new Date().toISOString().slice(0,10);
    const month = now.slice(0,7);
    
    // 猪场选项（确保已加载）
    const farmOpts = farmList.map(f=>`<option value="${f.id}" ${row.farm_id==f.id?'selected':''}>${f.name}</option>`).join('');
    const batchOpts = batchList.map(b=>`<option value="${b.id}" ${row.batch_id==b.id?'selected':''}>${b.batch_code} ${b.batch_name||''}</option>`).join('');
    const pigOpts = (cfg.pig_types||[]).map(p=>`<option value="${p}" ${row.pig_type===p?'selected':''}>${p}</option>`).join('');
    const barnTypeOpts = (cfg.barn_types||[]).map(t=>`<option value="${t}" ${row.barn_type===t?'selected':''}>${t}</option>`).join('');
    const roleOpts = (cfg.employee_roles||[]).map(r=>`<option value="${r}" ${row.role===r?'selected':''}>${r}</option>`).join('');
    const breedMethodOpts = (cfg.breed_methods||['本交','人工授精']).map(m=>`<option value="${m}" ${row.breed_method===m?'selected':''}>${m}</option>`).join('');
    const deathTypeOpts = (cfg.death_types||['死亡','淘汰']).map(t=>`<option value="${t}" ${row.death_type===t?'selected':''}>${t}</option>`).join('');
    const incomeTypeOpts = (cfg.income_types||[]).map(t=>`<option value="${t}" ${row.income_type===t?'selected':''}>${t}</option>`).join('');
    const costTypeOpts = (cfg.cost_categories||[]).map(t=>`<option value="${t}" ${row.cost_category===t?'selected':''}>${t}</option>`).join('');
    const immuneTypeOpts = (cfg.immune_types||['基础免疫','应激免疫','驱虫']).map(t=>`<option value="${t}" ${row.immune_type===t?'selected':''}>${t}</option>`).join('');
    const immuneMethodOpts = (cfg.immune_methods||['肌注','口服','滴鼻','喷雾']).map(m=>`<option value="${m}" ${row.immune_method===m?'selected':''}>${m}</option>`).join('');
    
    // 猪舍选项（异步加载）
    let barnOpts = '<option value="">请选择猪场</option>';
    if (row.farm_id) {
        try {
            const barns = (await request(`/barns?farm_id=${row.farm_id}`)).data||[];
            barnOpts = barns.map(b=>`<option value="${b.id}" ${row.barn_id==b.id?'selected':''}>${b.name} (${b.barn_type||''})</option>`).join('');
        } catch(e) {}
    }
    
    // 猪群选项
    let herdOpts = '<option value="">请选择猪群</option>';
    if (row.farm_id) {
        try {
            const herds = (await request(`/herds?farm_id=${row.farm_id}`)).data||[];
            herdOpts = herds.map(h=>`<option value="${h.id}" ${row.herd_id==h.id?'selected':''}>${h.herd_name||h.batch_no} (${h.pig_type||''})</option>`).join('');
        } catch(e) {}
    }
    
    const pages = {
        farm: `<div class="form-row"><div class="form-group"><label>猪场编码 *</label><input name="code" value="${row.code||''}" required></div><div class="form-group"><label>猪场名称 *</label><input name="name" value="${row.name||''}" required></div></div><div class="form-row"><div class="form-group"><label>地址</label><input name="address" value="${row.address||''}"></div><div class="form-group"><label>负责人</label><input name="manager" value="${row.manager||''}"></div></div><div class="form-row"><div class="form-group"><label>电话</label><input name="phone" value="${row.phone||''}"></div><div class="form-group"><label>存栏规模(头)</label><input name="stock_scale" type="number" value="${row.stock_scale||0}"></div></div><div class="form-row"><div class="form-group"><label>建成时间</label><input name="built_date" type="date" value="${row.built_date||''}"></div><div class="form-group"><label>占地面积(亩)</label><input name="area" type="number" step="0.1" value="${row.area||0}"></div></div><div class="form-row"><div class="form-group"><label>状态</label><select name="status"><option value="正常">正常</option><option value="停用">停用</option></select></div><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>`,
        
        barn: `<div class="form-row"><div class="form-group"><label>所属猪场 *</label><select name="farm_id" id="form-farm-select" required onchange="onFarmChangeForBarn(this.value)">${farmOpts||'<option value="">请先添加猪场</option>'}</select></div><div class="form-group"><label>猪舍编号</label><input name="barn_code" value="${row.barn_code||''}"></div></div><div class="form-row"><div class="form-group"><label>猪舍名称 *</label><input name="name" value="${row.name||''}" required></div><div class="form-group"><label>类型</label><select name="barn_type">${barnTypeOpts}</select></div></div><div class="form-row"><div class="form-group"><label>面积(m²)</label><input name="area" type="number" step="0.1" value="${row.area||0}"></div><div class="form-group"><label>存栏容量</label><input name="capacity" type="number" value="${row.capacity||0}"></div></div><div class="form-row"><div class="form-group"><label>状态</label><select name="status"><option value="正常">正常</option><option value="空置">空置</option><option value="维修中">维修中</option></select></div><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>
            ${row.farm_id&&row.barn_id?`<script>setTimeout(()=>onFarmChangeForBarn('${row.farm_id}','${row.barn_id}'),200);<\/script>`:''}`,
        
        herd: `<div class="form-row"><div class="form-group"><label>所属批次 <span class="required">*</span></label><select name="batch_id" id="form-batch-select-h" required onchange="onBatchChangeForHerd(this.value)">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>所属猪场</label><select name="farm_id" id="form-farm-select-h" onchange="onFarmChangeForHerd(this.value)">${farmOpts}</select></div></div><div class="form-row"><div class="form-group"><label>猪群编号</label><input name="herd_code" value="${row.herd_code||''}" placeholder="自动生成，可留空"></div><div class="form-group"><label>猪群名称</label><input name="herd_name" value="${row.herd_name||''}"></div></div><div class="form-row"><div class="form-group"><label>猪只类型</label><select name="pig_type">${pigOpts}</select></div><div class="form-group"><label>所属猪舍</label><select name="barn_id" id="form-barn-select-h"><option value="">请先选猪场</option></select></div></div><div class="form-row"><div class="form-group"><label>数量（头）</label><input name="quantity" type="number" value="${row.quantity||0}"></div><div class="form-group"><label>存栏重量（kg）</label><input name="weight" type="number" step="0.1" value="${row.weight||0}"></div></div><div class="form-row"><div class="form-group"><label>日龄</label><input name="age_days" type="number" value="${row.age_days||0}"></div><div class="form-group"><label>入群日期</label><input name="in_date" type="date" value="${row.in_date||now}"></div></div><div class="form-row"><div class="form-group"><label>状态（系统自动联动）</label><select name="status"><option value="存栏" ${row.status==='存栏'?'selected':''}>存栏</option><option value="已断奶" ${row.status==='已断奶'?'selected':''}>已断奶</option><option value="已转舍" ${row.status==='已转舍'?'selected':''}>已转舍</option><option value="已销售" ${row.status==='已销售'?'selected':''}>已销售</option><option value="已死亡" ${row.status==='已死亡'?'selected':''}>已死亡</option><option value="已淘汰" ${row.status==='已淘汰'?'selected':''}>已淘汰</option><option value="已清群" ${row.status==='已清群'?'selected':''}>已清群</option><option value="免疫中" ${row.status==='免疫中'?'selected':''}>免疫中</option></select></div><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>
            ${row.batch_id?`<script>setTimeout(()=>{onBatchChangeForHerd('${row.batch_id}','${row.barn_id||''}');},200);<\/script>`:''}`,
        
        batch: `<div class="form-row"><div class="form-group"><label>批次编号</label><input name="batch_code" value="${row.batch_code||'(自动生成)'}" readonly style="background:#f0f0f0"></div><div class="form-group"><label>批次名称 <span class="required">*</span></label><input name="batch_name" value="${row.batch_name||''}" required placeholder="如：2025年第一批次育肥猪"></div></div><div class="form-row"><div class="form-group"><label>所属猪场 <span class="required">*</span></label><select name="farm_id" required>${farmOpts}</select></div><div class="form-group"><label>批次类型 <span class="required">*</span></label><select name="batch_type" required><option value="配种批次" ${row.batch_type==='配种批次'?'selected':''}>配种批次</option><option value="分娩批次" ${row.batch_type==='分娩批次'?'selected':''}>分娩批次</option><option value="保育批次" ${row.batch_type==='保育批次'?'selected':''}>保育批次</option><option value="育肥批次" ${row.batch_type==='育肥批次'?'selected':''}>育肥批次</option></select></div></div><div class="form-row"><div class="form-group"><label>开始日期 <span class="required">*</span></label><input name="start_date" type="date" value="${row.start_date||now}" required></div><div class="form-group"><label>预计结束日期</label><input name="expected_end_date" type="date" value="${row.expected_end_date||''}"></div></div><div class="form-row"><div class="form-group"><label>头数</label><input name="quantity" type="number" value="${row.quantity||0}"></div><div class="form-group"><label>负责人</label><input name="manager" value="${row.manager||''}"></div></div><div class="form-row"><div class="form-group"><label>状态</label><select name="status"><option value="进行中" ${row.status==='进行中'?'selected':''}>进行中</option><option value="已完成" ${row.status==='已完成'?'selected':''}>已完成</option><option value="已清群" ${row.status==='已清群'?'selected':''}>已清群</option></select></div><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>`,
        
        employee: `<div class="form-row"><div class="form-group"><label>所属猪场 *</label><select name="farm_id" required>${farmOpts}</select></div><div class="form-group"><label>姓名 *</label><input name="name" value="${row.name||''}" required></div></div><div class="form-row"><div class="form-group"><label>职位</label><select name="role">${roleOpts}</select></div><div class="form-group"><label>部门</label><input name="dept" value="${row.dept||''}"></div></div><div class="form-row"><div class="form-group"><label>电话</label><input name="phone" value="${row.phone||''}"></div><div class="form-group"><label>状态</label><select name="status"><option value="在职">在职</option><option value="离职">离职</option></select></div></div>`,
        
        breeding: `<div class="form-row"><div class="form-group"><label>批次 <span class="required">*</span></label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','prod-herd-sel','','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>母猪号 *</label><input name="sow_code" value="${row.sow_code||''}" required></div></div><div class="form-row"><div class="form-group"><label>公猪号</label><input name="boar_code" value="${row.boar_code||''}"></div><div class="form-group"><label>配种日期 *</label><input name="breed_date" type="date" value="${row.breed_date||now}" required></div></div><div class="form-row"><div class="form-group"><label>配种方式</label><select name="breed_method">${breedMethodOpts}</select></div><div class="form-group"><label>预产日期</label><input name="expected_date" type="date" value="${row.expected_date||''}"></div></div><div class="form-row"><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div><div class="form-group"><label>状态</label><select name="status"><option value="已配种">已配种</option><option value="返情">返情</option><option value="空怀">空怀</option><option value="已分娩">已分娩</option><option value="流产">流产</option></select></div></div><div class="form-row"><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>`,
        
        farrowing: `<div class="form-row"><div class="form-group"><label>批次 <span class="required">*</span></label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','prod-herd-sel','','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>母猪号 *</label><input name="sow_code" value="${row.sow_code||''}" required></div></div><div class="form-row"><div class="form-group"><label>产仔日期 *</label><input name="farrow_date" type="date" value="${row.farrow_date||now}" required></div><div class="form-group"><label>总仔</label><input name="total_born" type="number" value="${row.total_born||0}"></div></div><div class="form-row"><div class="form-group"><label>活仔</label><input name="alive_born" type="number" value="${row.alive_born||0}"></div><div class="form-group"><label>健仔</label><input name="healthy_count" type="number" value="${row.healthy_count||0}"></div></div><div class="form-row"><div class="form-group"><label>死胎</label><input name="dead_born" type="number" value="${row.dead_born||0}"></div><div class="form-group"><label>木乃伊</label><input name="mummy" type="number" value="${row.mummy||0}"></div></div><div class="form-row"><div class="form-group"><label>弱仔</label><input name="weak" type="number" value="${row.weak||0}"></div><div class="form-group"><label>均重(kg)</label><input name="avg_weight" type="number" step="0.1" value="${row.avg_weight||0}"></div><div class="form-group"><label>窝重(kg)</label><input name="litter_weight" type="number" step="0.01" value="${row.litter_weight||0}"></div></div><div class="form-row"><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>`,
        
        weaning: `<div class="form-row"><div class="form-group"><label>批次</label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','prod-herd-sel','','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>母猪号</label><input name="sow_code" value="${row.sow_code||''}"></div></div><div class="form-row"><div class="form-group"><label>断奶日期 *</label><input name="wean_date" type="date" value="${row.wean_date||now}" required></div><div class="form-group"><label>断奶头数</label><input name="weaned_count" type="number" value="${row.weaned_count||0}"></div></div><div class="form-row"><div class="form-group"><label>均重(kg)</label><input name="avg_weight" type="number" step="0.1" value="${row.avg_weight||0}"></div></div><div class="form-group full"><label>备注</label><textarea name="notes">${row.notes||''}</textarea></div>`,
        
        transfer: `<div class="form-row"><div class="form-group"><label>批次 <span class="required">*</span></label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','prod-herd-sel','prod-barn-sel','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>猪群</label><select name="herd_id" id="prod-herd-sel" onchange="onHerdChangeForProd('prod-herd-sel','prod-pig-type','prod-barn-sel','prod-qty');"><option value="">请先选批次</option></select></div></div><div class="form-row"><div class="form-group"><label>猪只类型</label><select name="pig_type" id="prod-pig-type">${pigOpts}</select></div><div class="form-group"><label>数量</label><input name="quantity" id="prod-qty" type="number" value="${row.quantity||0}"></div></div><div class="form-row"><div class="form-group"><label>转出猪舍</label><input name="from_barn" value="${row.from_barn||''}"></div><div class="form-group"><label>转入猪舍</label><select name="to_barn" id="prod-barn-sel"><option value="">请先选批次</option></select></div></div><div class="form-row"><div class="form-group"><label>日期 *</label><input name="transfer_date" type="date" value="${row.transfer_date||now}" required></div><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div></div><div class="form-group full"><label>备注</label><textarea name="notes">${row.notes||''}</textarea></div>`,
        
        death: `<div class="form-row"><div class="form-group"><label>批次 <span class="required">*</span></label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','prod-herd-sel','prod-barn-sel','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>猪群</label><select name="herd_id" id="prod-herd-sel" onchange="onHerdChangeForProd('prod-herd-sel','prod-pig-type','prod-barn-sel','prod-qty');"><option value="">请先选批次</option></select></div></div><div class="form-row"><div class="form-group"><label>猪只类型</label><select name="pig_type" id="prod-pig-type">${pigOpts}</select></div><div class="form-group"><label>数量</label><input name="quantity" id="prod-qty" type="number" value="${row.quantity||0}"></div></div><div class="form-row"><div class="form-group"><label>猪舍</label><select name="barn_id" id="prod-barn-sel"><option value="">请先选批次</option></select></div><div class="form-group"><label>类型</label><select name="death_type">${deathTypeOpts}</select></div></div><div class="form-row"><div class="form-group"><label>原因</label><input name="reason" value="${row.reason||''}"></div><div class="form-group"><label>日期 *</label><input name="death_date" type="date" value="${row.death_date||now}" required></div></div><div class="form-row"><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div></div><div class="form-group full"><label>备注</label><textarea name="notes">${row.notes||''}</textarea></div>`,
        
        sales: `<div class="form-row"><div class="form-group"><label>批次 <span class="required">*</span></label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','prod-herd-sel','prod-barn-sel','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>猪群</label><select name="herd_id" id="prod-herd-sel" onchange="onHerdChangeForProd('prod-herd-sel','prod-pig-type','prod-barn-sel','prod-qty');"><option value="">请先选批次</option></select></div></div><div class="form-row"><div class="form-group"><label>猪只类型 *</label><select name="pig_type" id="prod-pig-type" required>${pigOpts}</select></div><div class="form-group"><label>数量 *</label><input name="quantity" id="prod-qty" type="number" value="${row.quantity||0}" required></div></div><div class="form-row"><div class="form-group"><label>猪舍</label><select name="barn_id" id="prod-barn-sel"><option value="">请先选批次</option></select></div><div class="form-group"><label>总重量(kg)</label><input name="total_weight" type="number" step="0.1" value="${row.total_weight||0}"></div></div><div class="form-row"><div class="form-group"><label>单价(元/kg)</label><input name="unit_price" type="number" step="0.01" value="${row.unit_price||0}"></div><div class="form-group"><label>买家</label><input name="buyer" value="${row.buyer||''}"></div></div><div class="form-row"><div class="form-group"><label>日期 *</label><input name="sale_date" type="date" value="${row.sale_date||now}" required></div><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div></div><div class="form-row"><div class="form-group"><label>备注</label><input name="notes" value="${row.notes||''}"></div></div>`,
        
        income: `<div class="form-row"><div class="form-group"><label>收入类型 *</label><select name="income_type" required>${incomeTypeOpts}</select></div><div class="form-group"><label>金额 *</label><input name="amount" type="number" step="0.01" value="${row.amount||0}" required></div></div><div class="form-row"><div class="form-group"><label>月份 *</label><input name="month" value="${row.month||month}" required></div><div class="form-group"><label>日期</label><input name="record_date" type="date" value="${row.record_date||now}"></div></div><div class="form-row"><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div><div class="form-group"><label>描述</label><input name="description" value="${row.description||''}"></div></div><div class="form-group full"><label>备注</label><textarea name="notes">${row.notes||''}</textarea></div>`,
        
        cost: `<div class="form-row"><div class="form-group"><label>成本类型 *</label><select name="cost_category" required>${costTypeOpts}</select></div><div class="form-group"><label>金额 *</label><input name="amount" type="number" step="0.01" value="${row.amount||0}" required></div></div><div class="form-row"><div class="form-group"><label>月份 *</label><input name="month" value="${row.month||month}" required></div><div class="form-group"><label>日期</label><input name="record_date" type="date" value="${row.record_date||now}"></div></div><div class="form-row"><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div><div class="form-group"><label>描述</label><input name="description" value="${row.description||''}"></div></div><div class="form-group full"><label>备注</label><textarea name="notes">${row.notes||''}</textarea></div>`,
        
        'immune-plan': `<div class="form-row"><div class="form-group"><label>批次</label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForProd('prod-batch-sel','','','');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-row"><div class="form-group"><label>疫苗名称 <span class="required">*</span></label><input name="vaccine_name" value="${row.vaccine_name||''}" placeholder="如：猪瘟疫苗、口蹄疫疫苗"></div><div class="form-group"><label>免疫类型</label><input name="immune_type" value="${row.immune_type||''}" list="immune-type-list" placeholder="可自由输入，如：基础免疫、应激免疫、驱虫等"><datalist id="immune-type-list"><option value="基础免疫"><option value="应激免疫"><option value="驱虫"><option value="细菌苗"><option value="病毒苗"><option value="联苗"></datalist></div></div><div class="form-row"><div class="form-group"><label>应免日龄（天）</label><input name="immune_age" type="number" value="${row.immune_age||0}" placeholder="如：0、7、21"></div><div class="form-group"><label>免疫方式</label><select name="immune_method">${immuneMethodOpts}</select></div></div><div class="form-row"><div class="form-group"><label>剂量</label><input name="dosage" value="${row.dosage||''}" placeholder="如：1头份/头、2mL/头"></div><div class="form-group"><label>复免间隔（天）</label><input name="interval_days" type="number" value="${row.interval_days||0}" placeholder="首免后多少天复免"></div></div><div class="form-row"><div class="form-group"><label>状态</label><select name="status"><option value="启用">启用</option><option value="停用">停用</option></select></div><div class="form-group full"><label>备注</label><textarea name="notes" placeholder="补充说明...">${row.notes||''}</textarea></div>`,

        'immune-record': `<div class="form-row"><div class="form-group"><label>批次 <span class="required">*</span></label><select name="batch_id" id="prod-batch-sel" onchange="onBatchChangeForImmRec('prod-batch-sel','prod-herd-sel','prod-barn-sel','immune-farm-select');">${batchOpts||'<option value="">请先创建批次</option>'}</select></div><div class="form-group"><label>所属猪场</label><select name="farm_id" id="immune-farm-select" onchange="onFarmChangeForImmuneRec(this.value);">${farmOpts}</select></div></div><div class="form-row"><div class="form-group"><label>猪群 / 耳号</label><select name="herd_id" id="prod-herd-sel"><option value="">请先选择批次或猪场</option></select></div><div class="form-group"><label>猪舍</label><select name="barn_id" id="prod-barn-sel"><option value="">请先选择批次或猪场</option></select></div></div><div class="form-row"><div class="form-group"><label>免疫日期 <span class="required">*</span></label><input name="immune_date" type="date" value="${row.immune_date||now}" required></div><div class="form-group"><label>疫苗名称 <span class="required">*</span></label><input name="vaccine_name" value="${row.vaccine_name||''}" placeholder="如：猪瘟疫苗"></div></div><div class="form-row"><div class="form-group"><label>免疫类型</label><input name="immune_type" value="${row.immune_type||''}" list="irec-type-list" placeholder="可自由输入"><datalist id="irec-type-list"><option value="基础免疫"><option value="应激免疫"><option value="驱虫"><option value="细菌苗"><option value="病毒苗"><option value="联苗"></datalist></div><div class="form-group"><label>免前日龄</label><input name="immune_age" type="number" value="${row.immune_age||0}"></div></div><div class="form-row"><div class="form-group"><label>免疫数量</label><input name="quantity" type="number" value="${row.quantity||0}"></div><div class="form-group"><label>免疫方式</label><select name="immune_method">${immuneMethodOpts}</select></div></div><div class="form-row"><div class="form-group"><label>剂量</label><input name="dosage" value="${row.dosage||''}" placeholder="如：1头份/头"></div><div class="form-group"><label>不良反应</label><input name="adverse_reaction" value="${row.adverse_reaction||''}"></div></div><div class="form-row"><div class="form-group"><label>操作人</label><input name="operator" value="${row.operator||''}"></div><div class="form-group"><label>应免疫日期</label><input name="due_immune_date" type="date" value="${row.due_immune_date||''}"></div></div><div class="form-group full"><label>备注</label><textarea name="notes" placeholder="补充说明...">${row.notes||''}</textarea></div>`,
    };
    
    return pages[page] || '<div class="empty-state">表单未配置</div>';
}

// 猪场变化时联动猪舍
async function onFarmChangeForBarn(farmId, preselectBarnId) {
    const sel = document.getElementById('form-barn-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">加载中...</option>';
    try {
        const barns = (await request(`/barns?farm_id=${farmId}`)).data||[];
        sel.innerHTML = barns.length ? barns.map(b=>`<option value="${b.id}">${b.name} (${b.barn_type||''})</option>`).join('') : '<option value="">无猪舍</option>';
        if (preselectBarnId) sel.value = preselectBarnId;
    } catch(e) { sel.innerHTML = '<option value="">加载失败</option>'; }
}

// 选择批次后 → 自动填充猪场 + 猪舍
async function onBatchChangeForHerd(batchId, preselectBarnId) {
    if (!batchId) return;
    const batch = batchList.find(b => String(b.id) === String(batchId));
    if (!batch) return;
    const farmId = batch.farm_id;
    // 自动填充猪场下拉
    const farmSel = document.getElementById('form-farm-select-h');
    if (farmSel) farmSel.value = farmId;
    // 加载猪舍
    const sel = document.getElementById('form-barn-select-h');
    if (!sel) return;
    sel.innerHTML = '<option value="">加载中...</option>';
    try {
        const barns = (await request(`/barns?farm_id=${farmId}`)).data||[];
        sel.innerHTML = barns.length ? barns.map(b=>`<option value="${b.id}">${b.name} (${b.barn_type||''})</option>`).join('') : '<option value="">无猪舍</option>';
        if (preselectBarnId) sel.value = preselectBarnId;
    } catch(e) { sel.innerHTML = '<option value="">加载失败</option>'; }
}

async function onFarmChangeForHerd(farmId, preselectBarnId) {
    const sel = document.getElementById('form-barn-select-h');
    if (!sel) return;
    sel.innerHTML = '<option value="">加载中...</option>';
    try {
        const barns = (await request(`/barns?farm_id=${farmId}`)).data||[];
        sel.innerHTML = barns.length ? barns.map(b=>`<option value="${b.id}">${b.name} (${b.barn_type||''})</option>`).join('') : '<option value="">无猪舍</option>';
        if (preselectBarnId) sel.value = preselectBarnId;
    } catch(e) { sel.innerHTML = '<option value="">加载失败</option>'; }
}

// ===== 通用：批次选择 → 加载该批次下的猪群 + 自动填猪场 =====
async function onBatchChangeForProd(batchSelId, herdSelId, barnSelId, farmSelId) {
    const batchId = document.getElementById(batchSelId)?.value;
    if (!batchId) return;
    const batch = batchList.find(b => String(b.id) === String(batchId));
    if (!batch) return;
    // 自动填猪场
    if (farmSelId) {
        const farmEl = document.getElementById(farmSelId);
        if (farmEl) farmEl.value = batch.farm_id || '';
    }
    // 加载批次下猪群
    if (herdSelId) {
        const herdSel = document.getElementById(herdSelId);
        if (!herdSel) return;
        herdSel.innerHTML = '<option value="">加载中...</option>';
        try {
            const herds = (await request(`/herds?farm_id=${batch.farm_id || ''}`)).data||[];
            // 只显示属于该批次的猪群
            const filtered = herds.filter(h => String(h.batch_id) === String(batchId));
            herdSel.innerHTML = filtered.length
                ? filtered.map(h=>`<option value="${h.id}">${h.herd_name||h.herd_code||h.id} (${h.pig_type||''}, ${h.quantity||0}头)</option>`).join('')
                : '<option value="">该批次暂无猪群</option>';
        } catch(e) { herdSel.innerHTML = '<option value="">加载失败</option>'; }
    }
    // 加载猪舍
    if (barnSelId) {
        const barnSel = document.getElementById(barnSelId);
        if (!barnSel) return;
        barnSel.innerHTML = '<option value="">加载中...</option>';
        try {
            const barns = (await request(`/barns?farm_id=${batch.farm_id || ''}`)).data||[];
            barnSel.innerHTML = barns.length
                ? barns.map(b=>`<option value="${b.id}">${b.name} (${b.barn_type||''})</option>`).join('')
                : '<option value="">无猪舍</option>';
        } catch(e) { barnSel.innerHTML = '<option value="">加载失败</option>'; }
    }
}

// ===== 通用：猪群选择 → 自动填猪只类型/猪舍/数量 =====
async function onHerdChangeForProd(herdSelId, pigTypeSelId, barnSelId, qtyInputId) {
    const herdId = document.getElementById(herdSelId)?.value;
    if (!herdId) return;
    const herd = (await request(`/herds?farm_id=`)).data?.find(h=>String(h.id)===String(herdId));
    if (!herd) {
        // 加载全部猪群找
        const herds = (await request(`/herds`)).data||[];
        const h = herds.find(h=>String(h.id)===String(herdId));
        if (!h) return;
        if (pigTypeSelId) {
            const el = document.getElementById(pigTypeSelId);
            if (el) { el.value = h.pig_type || ''; }
        }
        if (barnSelId) {
            const el = document.getElementById(barnSelId);
            if (el) { el.value = h.barn_id || ''; }
        }
        if (qtyInputId) {
            const el = document.getElementById(qtyInputId);
            if (el) { el.value = h.quantity || 0; el.max = h.quantity || 9999; }
        }
        return;
    }
    if (pigTypeSelId) {
        const el = document.getElementById(pigTypeSelId);
        if (el) { el.value = herd.pig_type || ''; }
    }
    if (barnSelId) {
        const el = document.getElementById(barnSelId);
        if (el) { el.value = herd.barn_id || ''; }
    }
    if (qtyInputId) {
        const el = document.getElementById(qtyInputId);
        if (el) { el.value = herd.quantity || 0; el.max = herd.quantity || 9999; }
    }
}

async function onFarmChangeForImmune(farmId, preselectHerdId) {
    const sel = document.getElementById('immune-herd-select');
    if (!sel) return;
    sel.innerHTML = '<option value="">加载中...</option>';
    try {
        const herds = (await request(`/herds?farm_id=${farmId}`)).data||[];
        sel.innerHTML = herds.length ? herds.map(h=>`<option value="${h.id}">${h.herd_name||h.batch_no} (${h.pig_type||''})</option>`).join('') : '<option value="">无猪群</option>';
        if (preselectHerdId) sel.value = preselectHerdId;
    } catch(e) { sel.innerHTML = '<option value="">加载失败</option>'; }
}

// ============ 免疫记录表单联动 ============
async function onFarmChangeForImmuneRec(farmId, preselectHerdId, farmSelId) {
    // 支持旧ID(immune-rec-*)和新ID(prod-*)
    const barnSel = document.getElementById('immune-rec-barn-select') || document.getElementById('prod-barn-sel');
    const herdSel = document.getElementById('immune-rec-herd-select') || document.getElementById('prod-herd-sel');
    if (!farmId) {
        if (barnSel) barnSel.innerHTML = '<option value="">请先选择猪场</option>';
        if (herdSel) herdSel.innerHTML = '<option value="">请先选择猪场</option>';
        return;
    }
    // 若已选批次，优先用批次的farm_id
    const batchSel = document.getElementById('prod-batch-sel');
    let loadFarmId = farmId;
    if (batchSel && batchSel.value) {
        const batch = batchList.find(b => String(b.id) === String(batchSel.value));
        if (batch && batch.farm_id) loadFarmId = batch.farm_id;
    }
    if (barnSel) barnSel.innerHTML = '<option value="">加载中...</option>';
    if (herdSel) herdSel.innerHTML = '<option value="">加载中...</option>';
    (async () => {
        try {
            const barns = (await request(`/barns?farm_id=${loadFarmId}`)).data||[];
            let herds = (await request(`/herds?farm_id=${loadFarmId}`)).data||[];
            // 按批次过滤
            const batchId = batchSel ? batchSel.value : '';
            if (batchId) herds = herds.filter(h => String(h.batch_id) === String(batchId));
            if (barnSel) barnSel.innerHTML = barns.length ? barns.map(b=>`<option value="${b.id}">${b.name}</option>`).join('') : '<option value="">无猪舍</option>';
            if (herdSel) herdSel.innerHTML = herds.length ? herds.map(h=>`<option value="${h.id}">${h.herd_name||h.herd_code||''} (${h.pig_type||''},${h.quantity||0}头)</option>`).join('') : '<option value="">无猪群</option>';
            if (preselectHerdId && herdSel) herdSel.value = preselectHerdId;
        } catch(e) {
            if (barnSel) barnSel.innerHTML = '<option value="">加载失败</option>';
            if (herdSel) herdSel.innerHTML = '<option value="">加载失败</option>';
        }
    })();
}

// ============ 批量导入/导出 ============
let _importMode = false;

async function openImportModal() {
    await ensureFarmList();
    _importMode = true;
    const farmId = document.getElementById('sel-farm').value;
    const farmOpts = farmList.map(f=>`<option value="${f.id}">${f.name}</option>`).join('');
    document.getElementById('modal-title').textContent = '批量导入 - ' + getPageTitle(currentPage);
    document.getElementById('modal-body').innerHTML = `
        <div style="margin-bottom:16px;padding:12px;background:#e7f3ff;border-radius:6px;border:1px solid #b3d7ff">
            <p style="margin-bottom:8px"><strong>操作步骤：</strong></p>
            <p style="margin-bottom:4px">① <a href="/api/template/${currentPage}" target="_blank" style="color:#007bff;font-weight:500">点击下载导入模板</a>（请勿修改表头）</p>
            <p style="margin-bottom:4px">② 按模板格式填写数据</p>
            <p>③ 选择猪场后上传文件</p>
        </div>
        <div class="form-row">
            <div class="form-group"><label>所属猪场</label><select id="import-farm-id">${farmOpts}</select></div>
            <div class="form-group"><label>选择文件 <span style="color:red">*</span></label><input type="file" id="import-file" accept=".xlsx" style="padding:6px;border:1px solid #ddd;border-radius:4px;width:100%"></div>
        </div>
        <div id="import-progress" style="margin-top:12px;display:none"></div>`;
    if (farmId) document.getElementById('import-farm-id').value = farmId;
    document.getElementById('modal').classList.add('show');
    // 切换底部按钮为"开始导入"
    const saveBtn = document.getElementById('modal-save-btn');
    if (saveBtn) saveBtn.textContent = '开始导入';
}

async function doImport() {
    const fileInput = document.getElementById('import-file');
    const farmId = document.getElementById('import-farm-id')?.value || '';
    if (!fileInput.files.length) { toast('请选择文件', 'error'); return; }
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    if (farmId) formData.append('farm_id', farmId);
    
    document.getElementById('import-progress').style.display = 'block';
    document.getElementById('import-progress').innerHTML = '<div style="color:#007bff">正在导入，请稍候...</div>';
    try {
        const res = await fetch(`/api/import/${currentPage}`, { method:'POST', headers:{'Authorization':`Bearer ${TOKEN}`}, body: formData });
        const json = await res.json();
        if (json.code !== 0) throw new Error(json.msg);
        toast(json.msg);
        if (json.errors?.length) { const errDiv = document.createElement('div'); errDiv.style.color='#dc3545'; errDiv.style.marginTop='8px'; errDiv.innerHTML = json.errors.slice(0,5).map(e=>`<div>${e}</div>`).join(''); document.getElementById('import-progress').appendChild(errDiv); }
        setTimeout(()=>{ closeModal(); loadPage(currentPage); }, 1500);
    } catch(e) { toast('导入失败: '+e.message, 'error'); document.getElementById('import-progress').style.display='none'; }
}

async function exportCurrentList() {
    const farmId = document.getElementById('sel-farm').value;
    try {
        const res = await fetch(`${BASE}/export/list/${currentPage}?farm_id=${farmId}`, { headers:{'Authorization':`Bearer ${TOKEN}`} });
        if (!res.ok) throw new Error('导出失败');
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a'); a.href = url;
        a.download = `${getPageTitle(currentPage)}_${new Date().toISOString().slice(0,10)}.xlsx`;
        a.click(); URL.revokeObjectURL(url);
    } catch(e) { toast('导出失败: '+e.message, 'error'); }
}

// ============ 工具 ============
function fm(v) { return (parseFloat(v)||0).toLocaleString('zh-CN',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function n(v) { const f=parseFloat(v); return f||f===0?f.toFixed(2):'0.00'; }
function toast(msg, type='') {
    const t = document.getElementById('toast');
    t.textContent = msg; t.className = 'toast show'+(type?' '+type:'');
    setTimeout(()=>t.className='toast', 3000);
}
