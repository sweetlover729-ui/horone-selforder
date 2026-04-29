# 调节器维修保养自助下单平台

## 项目简介
调节器维修保养自助下单系统，包含客户端下单界面和管理控制台。

## 技术栈
- 前端：Vue 3 + Vite
- 控制台：Vue 3 + Vite
- 后端：Flask (Python)
- 数据库：SQLite

## 目录结构
```
horone.selforder/
├── frontend/           # 客户端源码
├── frontend-console/   # 控制台源码
├── backend/            # Flask后端
│   ├── app.py         # 主应用入口
│   ├── database.py    # 数据库模型
│   ├── pdf_generator.py
│   ├── routes_admin.py
│   ├── routes_client.py
│   ├── routes_console.py
│   └── venv/          # Python虚拟环境
├── database/           # 数据库文件
│   └── selforder.db
├── uploads/            # 上传文件
│   ├── orders/
│   └── pdfs/
└── dist/               # 构建产物
    ├── client/         # 客户端静态文件
    └── console/        # 控制台静态文件
```

## 启动命令
```bash
cd ~/localserver/horone.selforder/backend
./venv/bin/python app.py
```
服务启动在端口 3001

## 构建命令
```bash
# 客户端
cd ~/localserver/horone.selforder/frontend
npm run build

# 控制台
cd ~/localserver/horone.selforder/frontend-console
npm run build
```

## 数据库位置
`~/localserver/horone.selforder/database/selforder.db`

## 重要文件说明
- `backend/app.py` - 后端主入口
- `backend/routes_client.py` - 客户端API路由
- `backend/routes_console.py` - 控制台API路由
- `backend/routes_admin.py` - 管理API路由
- `backend/pdf_generator.py` - PDF生成器
- `frontend/dist/` - 客户端构建产物（已部署到 dist/client/）
- `frontend-console/dist/` - 控制台构建产物（已部署到 dist/console/）

## 域名配置
- 主站：https://horone.alautoai.cn
- 控制台：https://horone.alautoai.cn/console/
- API: https://horone.alautoai.cn/selforder-api/
