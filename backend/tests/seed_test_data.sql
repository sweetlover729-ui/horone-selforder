-- ================================================================================
-- CI Test Seed Data for horone.selforder
-- Run AFTER schema.sql tables are created
-- Provides minimal catalog + staff data for all test cases
-- ================================================================================

-- ═══════════════════════════════════════════════════════
-- Categories (required by service_types.category_id FK)
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
-- Product Types
-- ═══════════════════════════════════════════════════════
INSERT INTO public.product_types (id, name, categories, description, sort_order, is_active) VALUES
(1, '调节器', '一级头,二级头,备用二级头', '潜水调节器维修保养', 1, 1),
(2, 'BCD', 'BCD', '浮力调节器维修保养', 2, 1),
(4, '电脑表', '电脑表', '潜水电脑表维修保养', 3, 1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Brands
-- ═══════════════════════════════════════════════════════
INSERT INTO public.brands (id, name, description, sort_order, is_active) VALUES
(1, 'Scubapro', 'Scubapro 品牌', 1, 1),
(2, 'Apeks', 'Apeks 品牌', 2, 1),
(3, 'Mares', 'Mares 品牌', 3, 1),
(4, 'Poseidon', 'Poseidon 品牌', 4, 1),
(5, 'Atomic', 'Atomic 品牌', 5, 1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Models (id=79 needed by test_state_machine _create_order)
-- ═══════════════════════════════════════════════════════
INSERT INTO public.models (id, name, brand_id, category, is_active) VALUES
(79, 'MK25/S600', 1, '调节器', 1)
ON CONFLICT (id) DO NOTHING;

-- ═══════════════════════════════════════════════════════
-- Service Types (id=15 needed by all order creation tests)
-- ═══════════════════════════════════════════════════════
INSERT INTO public.service_types (id, product_type_id, name, description, base_price, category_id, is_active) VALUES
(15, 1, '标准套装保养', '调节器标准保养套装', 300.0, 3, 1),
(1,  1, '一级头保养', '一级头单独保养', 200.0, 5, 1),
(2,  1, '二级头保养', '二级头单独保养', 150.0, 4, 1),
(3,  2, 'BCD标准保养', 'BCD标准保养', 250.0, 2, 1),
(4,  4, '电脑表检测', '电脑表功能检测', 100.0, 6, 1)
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
SELECT setval('public.categories_id_seq', COALESCE((SELECT MAX(id) FROM public.categories), 1), true);
SELECT setval('public.product_types_id_seq', COALESCE((SELECT MAX(id) FROM public.product_types), 1), true);
SELECT setval('public.brands_id_seq', COALESCE((SELECT MAX(id) FROM public.brands), 1), true);
SELECT setval('public.models_id_seq', COALESCE((SELECT MAX(id) FROM public.models), 1), true);
SELECT setval('public.service_types_id_seq', COALESCE((SELECT MAX(id) FROM public.service_types), 1), true);
SELECT setval('public.staff_id_seq', COALESCE((SELECT MAX(id) FROM public.staff), 1), true);
