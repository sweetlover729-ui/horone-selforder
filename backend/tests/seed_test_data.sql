-- ================================================================================
-- CI Test Seed Data for horone.selforder
-- Run AFTER schema.sql tables are created
-- Provides minimal catalog + staff data for all test cases
-- Columns match actual PG schema (verified 2026-05-01)
-- ================================================================================

-- ═══════════════════════════════════════════════════════
-- Categories
-- ═══════════════════════════════════════════════════════
INSERT INTO public.categories (id, name) VALUES
(1, '备用二级头'),
(2, 'BCD'),
(3, '套装'),
(4, '二级头'),
(5, '一级头'),
(6, '面镜'),
(7, '呼吸管'),
(8, '脚蹼'),
(9, '湿衣'),
(10, '干衣')
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Product Types (id, name, sort_order, is_active, categories)
-- ═══════════════════════════════════════════════════════
INSERT INTO public.product_types (id, name, sort_order, is_active, categories) VALUES
(1, '调节器',  1, 1, '{一级头,二级头,备用二级头}'),
(2, 'BCD',     2, 1, '{BCD}'),
(4, '电脑表',  3, 1, '{电脑表}')
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Brands (id, product_type_id, name, is_active)
-- ═══════════════════════════════════════════════════════
INSERT INTO public.brands (id, product_type_id, name, is_active) VALUES
(1, 1, 'Scubapro', 1),
(2, 1, 'Apeks',    1),
(3, 1, 'Mares',    1),
(4, 1, 'Poseidon', 1),
(5, 1, 'Atomic',   1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Models (id, brand_id, name, category, is_active)
-- id=79 needed by test_state_machine _create_order
-- ═══════════════════════════════════════════════════════
INSERT INTO public.models (id, brand_id, name, category, is_active) VALUES
(79, 1, 'MK25/S600', '调节器', 1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Service Types (id, product_type_id, name, base_price, category_id, is_active)
-- id=15 needed by all order creation tests
-- ═══════════════════════════════════════════════════════
INSERT INTO public.service_types (id, product_type_id, name, base_price, category_id, is_active) VALUES
(15, 1, '标准套装保养', 300, 3, 1),
(1,  1, '一级头保养',  200, 5, 1),
(2,  1, '二级头保养',  150, 4, 1),
(3,  2, 'BCD标准保养', 250, 2, 1),
(4,  4, '电脑表检测',  100, 6, 1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Customers (id=1 required by FK constraints in admin/console tests)
-- phone=13900000001 matches conftest.py customer_token fixture
-- ═══════════════════════════════════════════════════════
INSERT INTO public.customers (id, phone, name, openid, is_dealer, discount_rate) VALUES
(1, '13900000001', '测试客户', NULL, 0, 100)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Orders (id=1 required by inventory part_usage FK tests)
-- ═══════════════════════════════════════════════════════
INSERT INTO public.orders (id, order_no, customer_id, status, payment_status) VALUES
(1, 'TEST-SEED-0001', 1, 'pending', 'unpaid')
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Staff users (for auth tests)
-- ═══════════════════════════════════════════════════════
INSERT INTO public.staff (id, username, password_hash, full_name, role, is_active) VALUES
(1, 'kent', '$2b$12$3PMcTcDcXoTjuLj1r10yTuATg82EudHu8yPF9I6M0Z01V0JEBh0iW', 'kent', 'admin', 1),
(2, 'test', '$2b$12$18y78BcWqQwYiB8Q4JNiQe8QPGyDjrpQ0KTVhU54oL11fV9/vwMS6', '测试技师', 'technician', 1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Reset sequences after ID insertions
-- ═══════════════════════════════════════════════════════
SELECT setval('public.categories_id_seq',    COALESCE((SELECT MAX(id) FROM public.categories),    1), true);
SELECT setval('public.product_types_id_seq', COALESCE((SELECT MAX(id) FROM public.product_types), 1), true);
SELECT setval('public.brands_id_seq',        COALESCE((SELECT MAX(id) FROM public.brands),        1), true);
SELECT setval('public.models_id_seq',        COALESCE((SELECT MAX(id) FROM public.models),        1), true);
SELECT setval('public.service_types_id_seq', COALESCE((SELECT MAX(id) FROM public.service_types), 1), true);
SELECT setval('public.staff_id_seq',         COALESCE((SELECT MAX(id) FROM public.staff),         1), true);
SELECT setval('public.customers_id_seq',     COALESCE((SELECT MAX(id) FROM public.customers),     1), true);
SELECT setval('public.orders_id_seq',        COALESCE((SELECT MAX(id) FROM public.orders),        1), true);
