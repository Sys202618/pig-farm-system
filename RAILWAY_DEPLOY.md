# 猪场管理系统 - Railway Deploy Guide

Platform: Railway (Singapore), /mo free credit, PostgreSQL included

## Steps
1. Register: railway.app, login with GitHub
2. Push code to GitHub
3. New Project - Deploy from GitHub repo
4. Add PostgreSQL (auto injects DATABASE_URL)
5. Set Start Command: cd backend && gunicorn -w 2 -b 0.0.0.0:PORT app:app
6. Wait 2-3 min, get public URL
7. Login: admin / admin123

## Key Notes
- Railway uses Nixpacks (auto-detect Python, no Dockerfile needed)
- PORT env var, NOT 5000
- Singapore region best for China access

## Deploy Steps (Detail)
1. railway.app - Login with GitHub
2. New Project - Deploy from GitHub repo - select pig-farm-system
3. Add PostgreSQL database (free 1GB)
4. Settings - Start Command: cd backend && gunicorn -w 2 -b 0.0.0.0:5000 app:app
5. Wait deploy, get URL

## Troubleshooting
Build failed: check requirements.txt exists
DB connection: confirm PostgreSQL added, DATABASE_URL injected
404: confirm start command is cd backend