# 快速开始 - 猪场管理系统云部署

## 5 分钟部署到公网

### 1. 推送代码到 GitHub

```bash
cd pig_farm_system
git remote add origin https://github.com/YOUR_USERNAME/pig-farm-system.git
git push -u origin master
```

### 2. 一键部署到 Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

或手动：
1. 访问 https://dashboard.render.com
2. New → Blueprint → 选择你的仓库
3. 等待 3 分钟自动部署

### 3. 访问系统

部署完成后，Render 会提供 URL：
```
https://pig-farm-system-xxx.onrender.com
```

默认账号：`admin` / `admin123`

---

## 特性

- ✅ 零服务器成本（Render 免费版）
- ✅ 多人在线协同
- ✅ 数据云端持久化
- ✅ 自动 HTTPS
- ✅ 手机/电脑/平板全平台访问

---

## 文件说明

```
pig_farm_system/
├── backend/
│   ├── app.py              # 主应用（业务逻辑未改动）
│   ├── db_adapter.py       # 新增：数据库适配层
│   ├── init_postgres.py    # 新增：PostgreSQL 初始化
│   └── requirements.txt    # 新增：依赖
├── frontend/               # 前端（未改动）
├── render.yaml             # Render 部署配置
└── DEPLOY.md               # 详细部署文档
```

---

## 技术栈

- **后端**: Flask + Gunicorn
- **数据库**: PostgreSQL (云端) / SQLite (本地)
- **前端**: 原生 HTML/CSS/JS
- **部署**: Render (PaaS)

---

版本: 1.0 | 更新日期: 2026-04-21
