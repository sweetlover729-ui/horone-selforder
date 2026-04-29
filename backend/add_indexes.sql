-- 数据库索引优化脚本
-- 执行时间: 2026-04-25
-- 目的: 优化常用查询性能

-- 1. orders 表索引
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_assigned_staff_id ON orders(assigned_staff_id);
CREATE INDEX IF NOT EXISTS idx_orders_status_created_at ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_customer_status ON orders(customer_id, status);

-- 2. tracking_nodes 表索引
CREATE INDEX IF NOT EXISTS idx_tracking_nodes_order_id ON tracking_nodes(order_id);
CREATE INDEX IF NOT EXISTS idx_tracking_nodes_order_code ON tracking_nodes(order_id, node_code);
CREATE INDEX IF NOT EXISTS idx_tracking_nodes_created_at ON tracking_nodes(created_at);

-- 3. order_items 表索引
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_type ON order_items(product_type_id);
CREATE INDEX IF NOT EXISTS idx_order_items_brand ON order_items(brand_id);
CREATE INDEX IF NOT EXISTS idx_order_items_model ON order_items(model_id);
CREATE INDEX IF NOT EXISTS idx_order_items_service_type ON order_items(service_type_id);

-- 4. special_service_records 表索引
CREATE INDEX IF NOT EXISTS idx_special_service_order_id ON special_service_records(order_id);
CREATE INDEX IF NOT EXISTS idx_special_service_status ON special_service_records(status);

-- 5. equipment_inspection_data 表索引
CREATE INDEX IF NOT EXISTS idx_equipment_inspection_order_item ON equipment_inspection_data(order_item_id);

-- 6. customers 表索引
CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_openid ON customers(openid);

-- 7. staff_tokens 表索引
CREATE INDEX IF NOT EXISTS idx_staff_tokens_token ON staff_tokens(token);
CREATE INDEX IF NOT EXISTS idx_staff_tokens_expires ON staff_tokens(expires_at);

-- 8. customer_tokens 表索引
CREATE INDEX IF NOT EXISTS idx_customer_tokens_token ON customer_tokens(token);
CREATE INDEX IF NOT EXISTS idx_customer_tokens_expires ON customer_tokens(expires_at);

-- 验证索引创建
SELECT tablename, indexname, indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('orders', 'tracking_nodes', 'order_items', 'special_service_records', 
                  'equipment_inspection_data', 'customers', 'staff_tokens', 'customer_tokens')
ORDER BY tablename, indexname;
