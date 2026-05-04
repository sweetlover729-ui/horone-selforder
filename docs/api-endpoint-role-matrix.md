# Horone.Selforder API 端点×角色权限矩阵

> 生成时间：2026-05-05  
> 总计：122 个 API 端点 | 3 个 Blueprint | 4 种角色

---

## 角色定义

| 角色 | 说明 | Token 类型 |
|------|------|-----------|
| **Public** | 无需登录，公开访问 | 无 |
| **Customer** | 终端客户（手机号/微信登录） | `Authorization: Bearer <token>` |
| **Staff** | 技师/前台/管理员（需有效员工账号） | `X-Staff-Token: <token>` |
| **Admin** | 超级管理员/管理员角色 | `X-Staff-Token` + `role IN (admin, super_admin)` |

---

## 一、Client Blueprint（客户端 — `/api/v1/client`）— 29 端点

### 认证（2）- Public
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| POST | `/auth/wechat-login` | wechat_login | Public | 微信登录（开发期含模拟） |
| POST | `/auth/phone-login` | phone_login | Public | 手机号+姓名登录 |

### 产品目录（5）- Public
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/products/types` | get_product_types | Public | 产品类型列表（级联筛选） |
| GET | `/products/brands` | get_brands | Public | 品牌列表 |
| GET | `/products/categories` | get_model_categories | Public | 型号分类列表 |
| GET | `/products/models` | get_models | Public | 型号列表（级联筛选） |
| GET | `/products/full` | get_full_products | Public | 全量产品数据一次性加载 |

### 服务与报价（4）- Customer
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/services` | get_services | Customer | 服务类型列表 |
| GET | `/special-services` | get_special_services | Customer | 专项服务列表 |
| GET | `/price` | get_order_price | Customer | 计算指定参数报价 |
| GET | `/prices` | get_all_prices | Customer | 所有价格覆盖列表 |

### 订单（10）- Customer
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| POST | `/orders` | create_order | Customer | ⚠️ 无token返回200+JSON错误（非401） |
| GET | `/orders/my` | get_my_orders | Customer | 我的订单列表 |
| GET | `/orders/<id>` | get_order_detail | Customer | 订单详情 |
| PUT | `/orders/<id>/edit` | edit_order | Customer | 编辑订单（仅confirmed/receiving） |
| PUT | `/orders/<id>/cancel` | cancel_order | Customer | 取消订单（仅confirmed/received） |
| PUT | `/orders/<id>/express` | update_express | Customer | 更新寄出快递 |
| POST | `/orders/<id>/special-service/respond` | respond_special_service | Customer | 响应专项服务报价 |
| GET | `/orders/<id>/special-services` | get_order_special_services | Customer | 获取订单专项服务列表 |
| GET | `/orders/<id>/pdf` | download_pdf | Customer | 下载维修报告PDF（支持query token） |
| POST | `/orders/<id>/pay` | mock_pay | Customer | 模拟支付 |

### 进度跟踪（6）- Customer
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/orders/<id>/tracking` | get_tracking | Customer | 订单追踪信息 |
| PUT | `/orders/<id>/return-express-client` | update_return_express_client | Customer | 客户填写回寄地址 |
| POST | `/orders/<id>/checkin` | store_checkin | Customer | 到店签到 |
| GET | `/orders/<id>/tracking/nodes` | get_tracking_nodes_only | Customer | 纯节点列表 |
| PUT | `/orders/<id>/tracking/node/<node_id>` | update_tracking_node | Customer | 更新追踪节点 |
| GET | `/orders/<id>/nodes/<node_id>/photo/<filename>` | client_get_node_photo | Customer | 获取节点照片 ✅防遍历 |

### 报告（2）- Customer
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/reports/overview` | reports_overview | Customer | 报告概览 |
| GET | `/reports/recent` | reports_recent | Customer | 最近报告 |

---

## 二、Console Blueprint（控制台 — `/api/v1/console`）— 32 端点

### 认证（3）
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| POST | `/auth/login` | staff_login | **Public** | 员工登录 |
| GET | `/auth/me` | get_me | Staff | 获取当前员工信息 |
| PUT | `/auth/password` | change_password | Staff | 修改密码 |

### 订单管理（5）- Staff
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/orders` | get_orders | Staff | 订单列表（多维筛选） |
| GET | `/orders/<id>` | get_order_detail | Staff | 订单详情 |
| DELETE | `/orders/<id>` | delete_order | Staff | 删除订单 |
| POST | `/orders/<id>/release` | release_order | Staff | 释放订单（取消技师分配） |
| PUT | `/orders/<id>/payment-status` | update_payment_status | Staff | 更新支付状态 |

### 仪表盘与报告（6）- Staff
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/dashboard/stats` | get_dashboard_stats | Staff | 仪表盘统计数据 |
| GET | `/dashboard/report` | get_dashboard_report | Staff | 仪表盘报表 |
| POST | `/orders/<id>/nodes/<node_id>/photo` | upload_node_photo | Staff | 上传节点照片 |
| GET | `/orders/<id>/nodes/<node_id>/photo/<filename>` | get_node_photo | Staff | 获取节点照片 ✅防遍历 |
| POST | `/orders/<id>/generate-report` | generate_report | Staff | 生成维修报告PDF |
| GET | `/orders/<id>/report-pdf` | get_report_pdf | Staff | 下载已生成报告 |

### 工作流（14）- Staff 🔒已加固
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| PUT | `/orders/<id>/receive` | receive_order | Staff | 接单 | `_check_order_access` ✅ |
| PUT | `/orders/<id>/inspect` | inspect_order | Staff | 检测 | `_check_order_access` ✅ |
| GET | `/service-items` | get_console_service_items | Staff | 服务项目列表 |
| PUT | `/orders/<id>/repair` | repair_order | Staff | 维修 | `_check_order_access` ✅ |
| POST | `/orders/<id>/special-service` | create_special_service | Staff | 创建专项服务 | `_check_order_access` ✅ |
| PUT | `/orders/<id>/special-service/<record_id>` | update_special_service | Staff | 更新专项服务 | `_check_order_access` ✅ |
| PUT | `/orders/<id>/qc` | qc_order | Staff | 质检 | `_check_order_access` ✅ |
| PUT | `/orders/<id>/return-express` | update_return_express | Staff | 回寄快递 | `_check_order_access` ✅ |
| PUT | `/orders/<id>/ship` | ship_order | Staff | 发货 | `_check_order_access` ✅ |
| PUT | `/orders/<id>/complete` | complete_order | Staff | 完成 | `_check_order_access` ✅ |
| GET | `/tech/orders` | tech_orders | Staff | 技师个人订单列表 |
| POST | `/tech/orders/<id>/accept` | tech_accept_order | Staff | 技师接单 |
| GET | `/orders/<id>/equipment-data` | get_equipment_data | Staff | 获取设备数据 | `_check_order_access` ✅ |
| POST/PUT | `/orders/<id>/equipment-data` | save_equipment_data | Staff | 保存设备数据 | `_check_order_access` ✅ |

### 模拟测试（3）- Staff
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| POST | `/simulate/create` | simulate_create_order | Staff | 模拟创建订单 |
| POST | `/simulate/<id>/step/<step>` | simulate_step | Staff | 模拟工作流步骤 |
| POST | `/simulate/cleanup` | simulate_cleanup | Staff | 清理模拟数据 |

---

## 三、Admin Blueprint（管理后台 — `/api/v1/console`）— 61 端点

> 全部端点受 `before_request` 钩子保护，自动验证 `require_admin(token)`

### 数据备份（3）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/backup` | export_backup | Admin | 导出全量JSON备份（密码脱敏） |
| POST | `/backup/restore` | restore_backup | Admin | 恢复备份（字段白名单校验） |
| POST | `/archive-cleanup` | archive_cleanup | Admin | 归档清理（日志不静默） |

### 产品目录（16）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/categories` | get_categories | Admin | 分类列表 |
| POST | `/categories` | create_category | Admin | 创建分类 |
| PUT | `/categories/<id>` | update_category | Admin | 更新分类 |
| DELETE | `/categories/<id>` | delete_category | Admin | 删除（关联model时拒绝） |
| GET | `/product-types` | get_product_types | Admin | 产品类型列表（级联过滤） |
| POST | `/product-types` | create_product_type | Admin | 创建产品类型 |
| PUT | `/product-types/<id>` | update_product_type | Admin | 更新产品类型 |
| DELETE | `/product-types/<id>` | delete_product_type | Admin | 删除（关联数据检查） |
| GET | `/brands` | get_brands | Admin | 品牌列表 |
| POST | `/brands` | create_brand | Admin | 创建品牌 |
| PUT | `/brands/<id>` | update_brand | Admin | 更新品牌 |
| DELETE | `/brands/<id>` | delete_brand | Admin | 删除（关联数据检查） |
| GET | `/models` | get_models | Admin | 型号列表 |
| POST | `/models` | create_model | Admin | 创建型号 |
| PUT | `/models/<id>` | update_model | Admin | 更新型号 |
| DELETE | `/models/<id>` | delete_model | Admin | 删除型号 |

### 客户管理（7）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/customers` | get_customers | Admin | 客户列表（分页） |
| GET | `/customers/<id>` | get_customer_detail | Admin | 客户详情 |
| PUT | `/customers/<id>` | update_customer | Admin | 更新客户 |
| DELETE | `/customers/<id>` | delete_customer | Admin | 删除客户 |
| POST | `/customers/<id>/addresses` | add_customer_address | Admin | 添加收货地址 |
| DELETE | `/customers/<id>/addresses/<addr_id>` | delete_customer_address | Admin | 删除收货地址 |
| GET | `/customers/list` | get_customers_list | Admin | 客户下拉列表（简洁） |

### 配件库存（10）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/parts` | list_parts | Admin | 配件列表 |
| POST | `/parts` | create_part | Admin | 创建配件 |
| GET | `/parts/<id>` | get_part | Admin | 配件详情 |
| PUT | `/parts/<id>` | update_part | Admin | 更新配件 |
| DELETE | `/parts/<id>` | delete_part | Admin | 删除配件 |
| POST | `/parts/<id>/stock-in` | stock_in | Admin | 入库 |
| POST | `/parts/<id>/stock-out` | stock_out | Admin | 出库 |
| GET | `/parts/low-stock` | low_stock_parts | Admin | 低库存预警 |
| GET | `/parts/<id>/stock-log` | part_stock_history | Admin | 库存日志 |
| GET | `/parts/usage/<order_id>` | order_part_usage | Admin | 订单配件使用 |

### 保养提醒（5）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/maintenance-reminders` | list_maintenance_reminders | Admin | 提醒列表 ✅SQL安全 |
| POST | `/maintenance-reminders` | create_manual_reminder | Admin | 手动创建提醒 |
| PUT | `/maintenance-reminders/<id>/reschedule` | reschedule_reminder | Admin | 重新排期 |
| PUT | `/maintenance-reminders/<id>/dismiss` | dismiss_reminder | Admin | 忽略提醒 |
| GET | `/maintenance-reminders/stats` | maintenance_stats | Admin | 提醒统计 |

### 定价管理（4）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/prices` | get_prices | Admin | 价格列表 |
| POST | `/prices` | create_price | Admin | 创建价格（UPSERT） |
| PUT | `/prices/<id>` | update_price | Admin | 更新价格 |
| DELETE | `/prices/<id>` | delete_price | Admin | 删除价格 |

### 服务管理（12）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/service-types` | get_service_types | Admin | 服务类型列表 |
| POST | `/service-types` | create_service_type | Admin | 创建服务类型 |
| PUT | `/service-types/<id>` | update_service_type | Admin | 更新服务类型 |
| DELETE | `/service-types/<id>` | delete_service_type | Admin | 删除（关联数据检查） |
| GET | `/service-items` | get_service_items | Admin | 服务项目列表 |
| POST | `/service-items` | create_service_item | Admin | 创建服务项目 |
| PUT | `/service-items/<id>` | update_service_item | Admin | 更新服务项目 |
| DELETE | `/service-items/<id>` | delete_service_item | Admin | 删除服务项目 |
| GET | `/special-services` | get_special_services | Admin | 专项服务列表 |
| POST | `/special-services` | create_special_service | Admin | 创建专项服务 |
| PUT | `/special-services/<id>` | update_special_service | Admin | 更新专项服务 |
| DELETE | `/special-services/<id>` | delete_special_service | Admin | 删除专项服务 |

### 员工管理（4）- Admin
| 方法 | 路径 | 函数 | 角色 | 备注 |
|------|------|------|------|------|
| GET | `/staff` | get_staff | Admin | 员工列表 |
| POST | `/staff` | create_staff | Admin | 创建员工 |
| PUT | `/staff/<id>` | update_staff | Admin | 更新员工（禁止自我禁用） |
| DELETE | `/staff/<id>` | delete_staff | Admin | 删除员工（清理关联+FK） |

---

## 汇总统计

| Blueprint | Public | Customer | Staff | Admin | 合计 |
|-----------|--------|----------|-------|-------|------|
| Client `/api/v1/client` | 7 | 22 | 0 | 0 | **29** |
| Console `/api/v1/console` | 1 | 0 | 31 | 0 | **32** |
| Admin `/api/v1/console` | 0 | 0 | 0 | 61 | **61** |
| **合计** | **8** | **22** | **31** | **61** | **122** |

---

## 安全加固记录

| 加固项 | 涉及端点 | 提交 |
|--------|---------|------|
| `_check_order_access()` 技师越权防护 | workflow 11端点 | `89cd3cb` |
| DELETE 级联检查（拒绝而非静默成功） | catalog 4 + services 4 | `89cd3cb` |
| edit_order 自动重算金额 | client orders 1 | `89cd3cb` |
| 备份脱敏 + 恢复白名单校验 | backup_restore 2 | `89cd3cb` + 追加 |
| f-string SQL → psycopg2.sql | maintenance 2 | `1d9d0e5` |
| 生产 CORS 收紧 + 调试环境变量 | app.py | `1d9d0e5` |
| 照片路径防遍历 `os.path.basename` | client + console 各1 | `1d9d0e5` |
| 归档清理错误日志化 | backup_restore 1 | `1d9d0e5` |
| 生产错误不返回traceback + str(e)通用化 | error_handlers | `89cd3cb` |
| 员工删除清空 `orders.assigned_staff_id` | staff 1 | `89cd3cb` |
| 订单详情 `assigned_staff_id` 归属校验 | console orders 1 | `89cd3cb` |

---

## 已知瑕疵

| 问题 | 位置 | 严重度 |
|------|------|--------|
| `create_order` 无token返回200而非401 | `orders.py:POST /orders` | 🟡 低 |
| admin蓝图内路由仍有冗余 `validate_staff_token` 调用 | catalog/services等 | 🟢 无害 |
| 部分端点有双重认证（before_request + inline） | admin全部 | 🟢 无害 |
