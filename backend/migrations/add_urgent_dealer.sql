-- 加急服务和经销商功能迁移脚本
-- 执行时间: 2026-04-25

-- 1. orders表添加加急服务字段
ALTER TABLE orders ADD COLUMN IF NOT EXISTS urgent_service INTEGER DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS urgent_fee REAL DEFAULT 0;

-- 2. customers表添加经销商字段
ALTER TABLE customers ADD COLUMN IF NOT EXISTS is_dealer INTEGER DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS discount_rate REAL DEFAULT 100;

-- 3. order_items表添加折扣相关字段（记录实际应用的折扣）
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS discount_rate REAL DEFAULT 100;
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS final_price REAL DEFAULT 0;

-- 4. 添加注释说明
COMMENT ON COLUMN orders.urgent_service IS '是否加急服务 0=否 1=是';
COMMENT ON COLUMN orders.urgent_fee IS '加急费用金额';
COMMENT ON COLUMN customers.is_dealer IS '是否经销商 0=否 1=是';
COMMENT ON COLUMN customers.discount_rate IS '折扣比例，如85表示85折';
COMMENT ON COLUMN order_items.discount_rate IS '该明细应用的折扣比例';
COMMENT ON COLUMN order_items.final_price IS '折扣后的实际单价';

-- 5. 添加索引
CREATE INDEX IF NOT EXISTS idx_orders_urgent ON orders(urgent_service);
CREATE INDEX IF NOT EXISTS idx_customers_dealer ON customers(is_dealer);

-- 6. 验证
SELECT 'orders columns' as check_item, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'orders' AND column_name IN ('urgent_service', 'urgent_fee');
