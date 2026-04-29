-- 产品类别系统改造迁移脚本
-- 执行时间: 2026-04-25

-- 1. 创建 categories 表（产品类别/类型）
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 创建 model_categories 关联表（型号-类别多对多）
CREATE TABLE IF NOT EXISTS model_categories (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE(model_id, category_id)
);

-- 3. 从现有 models.category 数据导入 categories
INSERT INTO categories (name, sort_order, is_active)
SELECT DISTINCT 
    category as name,
    CASE category
        WHEN '一级头' THEN 1
        WHEN '二级头' THEN 2
        WHEN '备用二级头' THEN 3
        WHEN '套装' THEN 4
        WHEN '背飞' THEN 5
        WHEN '电脑表' THEN 6
        ELSE 99
    END as sort_order,
    1 as is_active
FROM models 
WHERE category IS NOT NULL AND category != ''
ON CONFLICT (name) DO NOTHING;

-- 4. 建立 model_categories 关联
INSERT INTO model_categories (model_id, category_id)
SELECT m.id, c.id
FROM models m
JOIN categories c ON m.category = c.name
WHERE m.category IS NOT NULL AND m.category != ''
ON CONFLICT DO NOTHING;

-- 5. 添加索引
CREATE INDEX IF NOT EXISTS idx_model_categories_model_id ON model_categories(model_id);
CREATE INDEX IF NOT EXISTS idx_model_categories_category_id ON model_categories(category_id);

-- 6. 验证数据
SELECT 'categories count' as check_item, COUNT(*) as cnt FROM categories
UNION ALL
SELECT 'model_categories count', COUNT(*) FROM model_categories
UNION ALL
SELECT 'models with category', COUNT(*) FROM models WHERE category IS NOT NULL;
