# 猪场管理系统 - 云部署指南

## 部署平台：Render (https://render.com)

### 1. 注册 Render 账号
- 访问 https://dashboard.render.com
- 用 GitHub 账号登录（推荐）

### 2. 创建 PostgreSQL 数据库
1. 在 Render Dashboard 点击 "New +" → "PostgreSQL"
2. 填写信息：
   - Name: `pig-farm-db`
   - Database: `pigfarm`
   - User: 自动生成
   - Plan: Free
3. 点击 "Create Database"
4. 等待创建完成，复制 **Internal Database URL**

### 3. 部署 Web 服务

#### 方式 A：Blueprints（推荐，一键部署）
1. 将本代码推送到 GitHub 仓库
2. 在 Render Dashboard → "Blueprints" → "New Blueprint Instance"
3. 选择你的 GitHub 仓库
4. Render 会自动读取 `render.yaml` 并创建服务和数据库

#### 方式 B：手动部署
1. 在 Render Dashboard 点击 "New +" → "Web Service"
2. 连接你的 GitHub 仓库
3. 配置：
   - **Name**: `pig-farm-system`
   - **Runtime**: Python 3
   - **Build Command**: 
     ```
     pip install -r backend/requirements.txt && python backend/init_postgres.py
     ```
   - **Start Command**: 
     ```
     gunicorn -w 2 -b 0.0.0.0:$PORT backend.app:app
     ```
4. 添加环境变量：
   - `DATABASE_URL`: 从 PostgreSQL 服务复制的 Internal Database URL
5. 点击 "Create Web Service"

### 4. 访问系统
- 部署完成后，Render 会提供一个 URL：`https://pig-farm-system-xxxx.onrender.com`
- 默认账号：`admin` / `admin123`

### 5. 特性
- ✅ 多人在线访问
- ✅ 数据云端持久化（PostgreSQL）
- ✅ 自动 HTTPS
- ✅ 免费额度：每月 750 小时运行时间（足够 24/7 运行）
- ⚠️ 免费数据库 30 天无活动会被删除（数据备份见下方）

### 6. 数据备份
```bash
# 导出数据
pg_dump $DATABASE_URL > backup.sql

# 导入数据
psql $DATABASE_URL < backup.sql
```

### 7. 更新部署
推送代码到 GitHub，Render 会自动重新部署。

---

## 本地开发（SQLite 模式）
```bash
cd backend
pip install -r requirements.txt
python app.py
# 访问 http://127.0.0.1:5000
```

## 技术变更说明
- 数据库层：新增 `db_adapter.py` 兼容 SQLite/PostgreSQL
- SQL 方言转换：`?` → `%s`, `datetime('now')` → `NOW()`
- 表结构：`init_postgres.py` 创建 PostgreSQL 兼容的表
- 原有业务逻辑：完全未改动
