# 猪场管理系统 - Zeabur 部署指南

## 部署步骤（5 分钟上线）

### 第一步：注册 Zeabur

1. 访问 https://zeabur.com
2. 点击 "Sign in with GitHub"（用 GitHub 账号登录）
3. 登录后进入 Dashboard

### 第二步：推送代码到 GitHub

```bash
cd C:\Users\shiyunshu\.qclaw\workspace-agent-626766d1\pig_farm_system

# 如果还没有 GitHub 仓库：
# 1. 先在 https://github.com/new 创建一个新仓库（如 pig-farm-system）
# 2. 然后执行：
git remote add origin https://github.com/你的用户名/pig-farm-system.git
git push -u origin master
```

### 第三步：在 Zeabur 创建项目

1. Dashboard → **"Create Project"**
2. 输入项目名：`pig-farm-system`
3. 选择 Region：**Hong Kong**（香港节点，国内访问最快）

### 第四步：添加 PostgreSQL 数据库

1. 项目中点击 **"Add Service"** → **"Prebuilt"** → **"PostgreSQL"**
2. 等待数据库创建完成（约 30 秒）
3. 创建后 Zeabur 自动注入 `POSTGRES_URL` 环境变量

### 第五步：添加 Web 服务

1. 项目中点击 **"Add Service"** → **"Git"** → 选择你的 GitHub 仓库
2. Zeabur 自动检测到 `zbpack.json` 配置
3. 无需手动配置，自动构建部署

### 第六步：配置域名

1. 点击 Web Service → **"Networking"** 标签
2. 点击 **"Generate Domain"** 生成免费域名
3. 得到类似：`pig-farm-system-xxx.zeabur.app`

### 第七步：验证

浏览器打开生成的域名，测试：
- ✅ 登录：`admin` / `admin123`
- ✅ 数据看板
- ✅ 各项功能

---

## 架构说明

```
用户浏览器 → Zeabur CDN (香港) → Gunicorn (Flask) → PostgreSQL
                    ↓
               静态文件 (frontend/)
```

### 数据库自动初始化

Flask 启动时检测 `DATABASE_URL` / `POSTGRES_URL`：
- **有值** → 连接 PostgreSQL，自动创建所有表 + 默认管理员
- **无值** → 使用本地 SQLite（开发模式）

### 环境变量

| 变量 | 来源 | 说明 |
|------|------|------|
| `DATABASE_URL` | Render | PostgreSQL 连接字符串 |
| `POSTGRES_URL` | Zeabur | PostgreSQL 连接字符串 |
| `PORT` | Zeabur | 自动设置 |

---

## 免费额度

| 资源 | 免费额度 |
|------|----------|
| Web 服务 | 每月 $5 免费额度 |
| PostgreSQL | 256MB 存储 |
| 带宽 | 1GB/月 |

⚠️ Zeabur 免费版服务会在无流量时休眠，首次访问需 5-10 秒唤醒。

---

## 数据备份

在 Zeabur Dashboard → PostgreSQL Service → **"Backups"** → 创建备份

或使用命令行：
```bash
# 导出
pg_dump $POSTGRES_URL > backup.sql

# 导入
psql $POSTGRES_URL < backup.sql
```

---

## 更新部署

推送代码到 GitHub → Zeabur 自动重新部署（约 1-2 分钟）

---

## 多人使用

部署完成后，将域名分享给团队成员：
- 每人用浏览器打开链接即可
- 支持多人同时在线编辑
- 数据实时同步（共享 PostgreSQL）
- 建议每人创建独立账号（当前只有 admin）

---

## 故障排查

**部署失败？**
- 检查 GitHub 仓库是否包含 `zbpack.json`
- 查看 Zeabur → Service → **"Deployments"** → Logs

**数据库连接失败？**
- 确认 PostgreSQL 服务已创建
- 检查 `POSTGRES_URL` 环境变量

**页面 404？**
- 确认 `frontend/` 目录在仓库中
- 检查 `zbpack.json` 的 build_command 是否包含 `cp -r frontend backend/frontend`

---

版本: 1.0 | 更新: 2026-04-21 | 平台: Zeabur (Hong Kong)
