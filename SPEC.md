# 潜水装备维修保养自助下单平台 - 技术规格文档

## 1. 项目概述

- **项目名称**：潜水装备维修保养自助下单平台
- **版本**：v2.0（2026-04-22）
- **客户端访问**：horone.alautoai.cn
- **控制台访问**：horone.alautoai.cn/console
- **项目路径**：/Users/wjjmac/localserver/horone.selforder/

## 2. 技术栈

- **前端**：Vue 3 + Vite + Element Plus + Axios
- **后端**：Python Flask + SQLite
- **图片存储**：本地文件系统
- **PDF生成**：ReportLab / pdfkit
- **快递对接**：顺丰丰桥API（后期接入，暂无账号）
- **微信通知**：服务通知（后期接入，暂无TemplateId）

## 3. 系统架构

### 3.1 两套入口
- **客户端**（horone.alautoai.cn）：面向潜水爱好者，微信扫码下单
- **控制台**（horone.alautoai.cn/console）：面向维修人员，密码登录

### 3.2 用户体系
| 角色 | 登录方式 | 入口 |
|------|---------|------|
| 客户 | 微信扫码（网页授权） | 客户端 |
| 维修人员 | 账号密码 | 控制台 |
| 管理员 | 账号密码 | 控制台 |

## 4. 数据库设计

### 4.1 表结构

```sql
-- 产品类型（如：调节器、BCD、背飞、湿衣等）
CREATE TABLE product_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,           -- 如"调节器"
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 品牌
CREATE TABLE brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_type_id INTEGER,
    name TEXT NOT NULL,
    country TEXT,
    website TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 型号（关联品牌）
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id INTEGER,
    name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 服务类型（固定价格）
CREATE TABLE service_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_type_id INTEGER,       -- 适用于哪类产品
    name TEXT NOT NULL,           -- 如"一级保养"、"二级保养"、"深度保养"
    description TEXT,
    base_price REAL DEFAULT 0,    -- 基础价格（元）
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 服务项目（保养步骤，如：拆解、清洗、更换O型圈、测压等）
CREATE TABLE service_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,           -- 如"更换O型圈"、"测压"
    description TEXT,
    is_required INTEGER DEFAULT 1, -- 是否必须完成
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 专项服务预设项目（可选服务，需额外收费）
CREATE TABLE special_services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,           -- 如"更换高压舱"、"阀门修复"
    description TEXT,
    preset_price REAL DEFAULT 0,  -- 预设价格（可调整）
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 客户表（微信授权后创建）
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    openid TEXT UNIQUE,           -- 微信openid
    nickname TEXT,
    avatar_url TEXT,
    phone TEXT,
    name TEXT,                     -- 真实姓名（收件用）
    address TEXT,                  -- 收件地址
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 订单主表
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no TEXT UNIQUE NOT NULL,  -- 订单号（格式：RMD-YYYYMMDD-XXXXXX）
    customer_id INTEGER,
    
    -- 收件人信息
    receiver_name TEXT,
    receiver_phone TEXT,
    receiver_address TEXT,
    
    -- 金额
    total_amount REAL DEFAULT 0,      -- 总价（含专项服务）
    freight_amount REAL DEFAULT 0,   -- 运费（客户自付）
    
    -- 状态
    status TEXT DEFAULT 'pending',   -- pending/unpaid/paid/receiving/repairing/
                                      -- special_service/ready/shipped/completed/cancelled
    
    -- 支付
    payment_status TEXT DEFAULT 'unpaid',  -- unpaid/paid
    payment_time TEXT,
    
    -- 快递（寄出）
    express_company TEXT,            -- 顺丰
    express_no TEXT,                 -- 客户寄出快递单号
    express_paid_by_customer INTEGER DEFAULT 1, -- 客户是否已付运费
    
    -- 快递（回寄）
    return_express_company TEXT,
    return_express_no TEXT,
    return_express_paid_by_customer INTEGER DEFAULT 0, -- 回寄不需客户付
    
    -- 备注
    customer_remark TEXT,            -- 客户备注
    staff_remark TEXT,              -- 员工备注
    
    -- 订单来源
    source TEXT DEFAULT 'wechat',    -- wechat/h5
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT                -- 完成时间（QC后）
);

-- 订单明细（每种产品/服务组合）
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_type_id INTEGER,
    brand_id INTEGER,
    model_id INTEGER,
    quantity INTEGER DEFAULT 1,
    
    -- 保养服务（客户选择）
    service_type_id INTEGER,        -- 客户选的服务类型（一保/二保/深度）
    
    -- 单项总价（服务费）
    item_price REAL DEFAULT 0,
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 订单追踪节点
CREATE TABLE tracking_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    node_code TEXT NOT NULL,        -- pending/unpaid_paid/received/inspecting/
                                    -- special_request/special_confirmed/
                                    -- repairing/qc_pass/shipped/completed
    node_name TEXT NOT NULL,        -- 节点名称（展示用）
    description TEXT,
    
    -- 维修人员填写
    staff_id INTEGER,
    staff_name TEXT,
    operate_time TEXT,             -- 填写时间（客户可见，维修人员选择）
    operate_note TEXT,              -- 备注
    
    -- 照片（JSON数组）
    photos TEXT,                    -- ["photo1.jpg","photo2.jpg"]
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 专项服务记录
CREATE TABLE special_service_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    order_item_id INTEGER,          -- 对应哪个订单明细
    
    special_service_id INTEGER,     -- 预设项目
    name TEXT,                       -- 服务名称（冗余）
    description TEXT,
    price REAL DEFAULT 0,            -- 本次定价
    
    status TEXT DEFAULT 'pending',  -- pending/confirmed/rejected/paid/completed
    staff_photos TEXT,               -- 照片
    staff_note TEXT,
    
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TEXT,               -- 客户确认时间
    paid_at TEXT                     -- 付款时间
);

-- 维修人员账号
CREATE TABLE staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'technician',  -- admin/technician/receptionist
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 价格配置表（按品牌型号服务类型定价，可覆盖默认价格）
CREATE TABLE price_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_type_id INTEGER,
    brand_id INTEGER,
    model_id INTEGER,
    service_type_id INTEGER,
    price REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_type_id, brand_id, model_id, service_type_id)
);

-- 系统设置
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 5. API接口设计

### 5.1 客户端API（/api/v1/client）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/wechat-login | 微信授权登录 |
| GET | /products/types | 获取产品类型列表 |
| GET | /products/brands?type_id= | 获取某类型下的品牌 |
| GET | /products/models?brand_id= | 获取某品牌下的型号 |
| GET | /services?type_id= | 获取某类型的服务项目及价格 |
| POST | /orders | 创建订单 |
| GET | /orders/:id | 获取订单详情（含追踪） |
| GET | /orders/my | 获取我的订单列表 |
| PUT | /orders/:id/express | 客户填写快递信息 |
| GET | /orders/:id/tracking | 获取订单追踪节点 |
| POST | /orders/:id/special-service/confirm | 客户确认/拒绝专项服务 |
| POST | /orders/:id/special-service/pay | 客户确认专项服务已付款 |
| GET | /orders/:id/pdf | 下载PDF（15天有效期检查）|

### 5.2 控制台API（/api/v1/console，需要登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 员工登录 |
| GET | /auth/me | 当前员工信息 |
| PUT | /auth/password | 修改密码 |
| GET | /orders | 订单列表（支持筛选） |
| GET | /orders/:id | 订单详情 |
| PUT | /orders/:id/status | 更新订单状态 |
| PUT | /orders/:id/receive | 确认收货 |
| POST | /orders/:id/tracking | 添加追踪节点（含图片）|
| POST | /orders/:id/special-service | 发起专项服务 |
| PUT | /orders/:id/special-service/:sid | 更新专项服务状态 |
| PUT | /orders/:id/qc | QC通过，生成PDF |
| PUT | /orders/:id/return-express | 填写回寄快递 |
| POST | /orders/:id/complete | 标记完成 |

### 5.3 数据管理API（/api/v1/console/admin）

| 方法 | 路径 | 说明 |
|------|------|------|
| CRUD | /products/types | 产品类型管理 |
| CRUD | /products/brands | 品牌管理 |
| CRUD | /products/models | 型号管理 |
| CRUD | /services/types | 服务类型管理 |
| CRUD | /services/items | 服务项目配置 |
| CRUD | /special-services | 专项服务预设 |
| CRUD | /prices | 价格配置 |

## 6. 订单状态流转

```
[pending] → [unpaid] → [paid] → [receiving] → [inspecting] 
→ [repairing] → [special_service?] → [qc_pass] → [shipped] → [completed]
                                        ↓
                              [special_confirmed] → [repairing]
```

节点说明：
- `pending`：客户填写中
- `unpaid`：待付款
- `paid`：已付款，等待寄件
- `receiving`：设备运输中（店方收件）
- `inspecting`：拆件检验中
- `repairing`：维修保养中
- `special_service`：专项服务（可多次循环）
- `ready`：维修完成待回寄
- `shipped`：已回寄快递
- `completed`：订单完成
- `cancelled`：已取消

## 7. PDF报告格式（参考潜水调节器维修保养完整记录.pdf）

包含内容：
1. 页眉：系统Logo + 报告标题 + 订单号 + 日期
2. 客户信息：姓名、联系方式
3. 设备信息：品牌、型号、数量
4. 服务项目明细（打勾清单）：每个服务项目有完成状态
5. 专项服务（如有）：名称、价格、照片
6. 维修前后照片对比
7. 维修人员签字 + 日期
8. 页脚：系统名称 + 联系方式

## 8. 客户端交互流程

```
1. 微信扫码 → 授权获取openid → 自动登录
2. 选择产品类型（卡片式）
3. 选择品牌（卡片式）
4. 选择型号（下拉选择）
5. 选择服务类型（卡片式，如一级保养298/二级保养498/深度保养698）
6. 填写数量（+/-按钮）
7. 填写收件人信息（姓名/电话/地址）
8. 备注（选填）
9. 确认订单 → 微信支付
10. 填写寄件快递（顺丰普快，单号）
11. 进度追踪（实时）
12. 收到专项服务通知 → 确认/拒绝 → 付款（如有）
13. 收到完成通知 → 查看PDF → 填写回寄快递
14. 确认收货 → 评价（可选）
```

## 9. 控制台交互流程

```
1. 账号登录
2. 收到新订单提醒（系统内）
3. 确认收货 → 上传拆件照片 → 填写检验说明
4. 开始维修保养 → 逐项完成服务项目 → 上传照片
5. [可选] 发起专项服务 → 填写价格/照片 → 等待客户确认付款
6. 维修完成 → 上传测试照片
7. QC PASS → 系统自动生成PDF → 上传最终照片
8. 填写回寄快递（顺丰，不付款）
9. 确认发出 → 更新追踪节点
10. 客户确认收货 → 订单完成
```

## 10. 文件存储结构

```
backend/
├── uploads/
│   ├── orders/
│   │   └── {order_id}/
│   │       ├── inspecting/   # 拆件照片
│   │       ├── repairing/     # 维修照片
│   │       ├── testing/       # 测试照片
│   │       ├── qc/           # QC照片
│   │       └── special/       # 专项服务照片
│   └── pdfs/
│       ├── {order_no}.pdf    # 永久保存
└── database/
    └── selforder.db
```

## 11. 已知限制与后期扩展

- 微信登录：待用户提供服务号AppID/AppSecret后接入
- 顺丰下单：待用户提供丰桥账号后接入
- 微信通知：待用户提供TemplateId后接入
- 图片存储：后期可一键迁移至腾讯云COS/华为云OBS/阿里云OSS

---

## 部署状态（2026-04-22 更新）

### 已上线
- 客户端：https://horone.alautoai.cn ✅
- 控制台：https://horone.alautoai.cn/console ✅
- 后端API：https://horone.alautoai.cn/selforder-api ✅

### 账号
- 控制台管理员：admin / admin123
- 控制台技师：tech01 / tech123

### 技术说明
- Nginx将 `/selforder-api/*` 代理到 `localhost:3001`
- Nginx将 `/selforder-api` 前缀剥离后转发给Flask（Flask路由用 `/api/v1/...`）
- 使用 `location ^~ /selforder-api` 确保正则location不干扰
- Authorization header 通过 curl 可以正确转发（Python urllib在小概率下有兼容问题）

### 启动命令
```bash
cd /Users/wjjmac/localserver/horone.selforder/backend
./venv/bin/python app.py
```

### Nginx配置
- 路径：`/usr/local/etc/nginx/servers/horone.alautoai.cn.conf`
- 前端dist（客户端）：`/Users/wjjmac/localserver/horone.selforder/dist/client`
- 前端dist（控制台）：`/Users/wjjmac/localserver/horone.selforder/dist/console`
- CDN 同步目录：`/usr/local/var/www/horone/selforder/client/`
