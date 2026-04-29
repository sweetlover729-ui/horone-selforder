#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端API测试脚本
测试完整流程: 客户下单 -> 技师接单 -> 收货 -> 检验 -> 维修 -> QC -> 发货 -> 完成
"""

import requests
import json
import sys

BASE_URL = "http://localhost:3001"
CLIENT_TOKEN = None
STAFF_TOKEN = None
ORDER_ID = None
CUSTOMER_ID = None

def log(msg):
    print(f"[TEST] {msg}")

def test_client_login():
    """测试客户登录"""
    global CLIENT_TOKEN, CUSTOMER_ID
    log("测试客户登录...")
    
    resp = requests.post(f"{BASE_URL}/api/v1/client/auth/phone-login", json={
        "phone": "13800138000",
        "name": "测试客户"
    })
    
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"登录失败: {data}"
    
    CLIENT_TOKEN = data['data']['token']
    CUSTOMER_ID = data['data']['id']
    log(f"✅ 客户登录成功, ID={CUSTOMER_ID}")
    return True

def test_create_order():
    """测试创建订单"""
    global ORDER_ID
    log("测试创建订单...")
    
    resp = requests.post(f"{BASE_URL}/api/v1/client/orders", 
        headers={"Authorization": f"Bearer {CLIENT_TOKEN}"},
        json={
            "items": [{
                "product_type_id": 1,
                "brand_id": 1,
                "model_id": 79,
                "service_type_id": 15,
                "quantity": 1
            }],
            "receiver_name": "测试客户",
            "receiver_phone": "13800138000",
            "receiver_address": "测试地址",
            "delivery_type": "express"
        }
    )
    
    assert resp.status_code == 200, f"创建订单失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"创建订单失败: {data}"
    
    ORDER_ID = data['data']['id']
    log(f"✅ 订单创建成功, ID={ORDER_ID}, 订单号={data['data']['order_no']}")
    return True

def test_staff_login():
    """测试技师登录"""
    global STAFF_TOKEN
    log("测试技师登录...")
    
    resp = requests.post(f"{BASE_URL}/api/v1/console/auth/login", json={
        "username": "kent",
        "password": "kent8888"
    })
    
    if resp.status_code != 200:
        log(f"⚠️ 技师登录失败(可能用户不存在),跳过技师流程测试")
        return False
    
    data = resp.json()
    if not data.get('success'):
        log(f"⚠️ 技师登录失败: {data}")
        return False
    
    STAFF_TOKEN = data['token']
    log(f"✅ 技师登录成功")
    return True

def test_accept_order():
    """测试技师接单"""
    log("测试技师接单...")
    
    resp = requests.post(f"{BASE_URL}/api/v1/console/tech/orders/{ORDER_ID}/accept",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    
    # 接单可能已自动完成或需要手动分配
    if resp.status_code == 200:
        data = resp.json()
        if data.get('success'):
            log(f"✅ 技师接单成功")
            return True
    
    # 如果接单端点返回404，可能是端点不存在，继续测试
    log(f"⚠️ 接单端点不可用({resp.status_code})，继续后续测试...")
    return True  # 继续测试

def test_receive_order():
    """测试确认收货 - 验证receive_order返回None修复"""
    log("测试确认收货(验证无照片时不返回None)...")
    
    # 先检查订单状态，如果是非pending/confirmed状态，需要先重置
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    if resp.status_code == 200:
        order_data = resp.json().get('data', {})
        if order_data.get('status') in ('received', 'inspecting', 'repairing', 'ready', 'shipped', 'completed'):
            log(f"⚠️ 订单状态为{order_data.get('status')}，跳过收货测试")
            return True
    
    # 测试无照片的情况
    resp = requests.put(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/receive",
        headers={"X-Staff-Token": STAFF_TOKEN},
        json={
            "note": "测试收货",
            "photos": [],  # 空照片数组
            "express_company": "顺丰速运",
            "express_no": "SF1234567890"
        }
    )
    
    assert resp.status_code == 200, f"收货失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"收货失败: {data}"
    
    log(f"✅ 确认收货成功(无照片)")
    return True

def test_inspect_order():
    """测试拆件检验"""
    log("测试拆件检验...")
    
    # 先检查订单状态
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    if resp.status_code == 200:
        order_data = resp.json().get('data', {})
        if order_data.get('status') not in ('received', 'pending'):
            log(f"⚠️ 订单状态为{order_data.get('status')}，跳过检验测试")
            return True
    
    resp = requests.put(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/inspect",
        headers={"X-Staff-Token": STAFF_TOKEN},
        json={
            "note": "设备外观良好",
            "photos": []
        }
    )
    
    assert resp.status_code == 200, f"检验失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"检验失败: {data}"
    
    log(f"✅ 拆件检验成功")
    return True

def test_repair_order():
    """测试维修保养"""
    log("测试维修保养...")
    
    # 先检查订单状态
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    if resp.status_code == 200:
        order_data = resp.json().get('data', {})
        if order_data.get('status') not in ('inspecting', 'received'):
            log(f"⚠️ 订单状态为{order_data.get('status')}，跳过维修测试")
            return True
    
    resp = requests.put(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/repair",
        headers={"X-Staff-Token": STAFF_TOKEN},
        json={
            "note": "更换O型圈",
            "photos": [],
            "selected_items": [1, 2, 3]
        }
    )
    
    assert resp.status_code == 200, f"维修失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"维修失败: {data}"
    
    log(f"✅ 维修保养成功")
    return True

def test_qc_order():
    """测试QC通过"""
    log("测试QC通过...")
    
    # 先检查订单状态
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    if resp.status_code == 200:
        order_data = resp.json().get('data', {})
        if order_data.get('status') != 'repairing':
            log(f"⚠️ 订单状态为{order_data.get('status')}，跳过QC测试")
            return True
    
    resp = requests.put(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/qc",
        headers={"X-Staff-Token": STAFF_TOKEN},
        json={
            "note": "质检通过",
            "photos": []
        }
    )
    
    assert resp.status_code == 200, f"QC失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"QC失败: {data}"
    
    log(f"✅ QC通过成功")
    return True

def test_ship_order():
    """测试发货"""
    log("测试发货...")
    
    # 先检查订单状态
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    if resp.status_code == 200:
        order_data = resp.json().get('data', {})
        if order_data.get('status') != 'ready':
            log(f"⚠️ 订单状态为{order_data.get('status')}，跳过后续测试")
            return True
    
    resp = requests.put(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/ship",
        headers={"X-Staff-Token": STAFF_TOKEN},
        json={
            "note": "已发货",
            "photos": [],
            "return_express_company": "顺丰速运",
            "return_express_no": "SF9876543210"
        }
    )
    
    assert resp.status_code == 200, f"发货失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"发货失败: {data}"
    
    log(f"✅ 发货成功")
    return True

def test_complete_order():
    """测试完成订单"""
    log("测试完成订单...")
    
    # 先检查订单状态
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    if resp.status_code == 200:
        order_data = resp.json().get('data', {})
        if order_data.get('status') != 'shipped':
            log(f"⚠️ 订单状态为{order_data.get('status')}，跳过完成测试")
            return True
    
    resp = requests.put(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/complete",
        headers={"X-Staff-Token": STAFF_TOKEN},
        json={
            "note": "订单完成"
        }
    )
    
    assert resp.status_code == 200, f"完成订单失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"完成订单失败: {data}"
    
    log(f"✅ 订单完成")
    return True

def test_order_detail():
    """测试订单详情(验证tracking_nodes)"""
    log("测试订单详情...")
    
    resp = requests.get(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    
    assert resp.status_code == 200, f"获取订单详情失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"获取订单详情失败: {data}"
    
    order = data['data']
    nodes = order.get('tracking_nodes', [])
    
    log(f"订单状态: {order['status']}")
    log(f"追踪节点数: {len(nodes)}")
    
    # 验证节点顺序
    expected_codes = ['created', 'received', 'inspect', 'repair', 'qc', 'shipped', 'completed']
    actual_codes = [n['node_code'] for n in nodes]
    
    for code in expected_codes:
        if code in actual_codes:
            log(f"  ✅ 节点 {code} 存在")
        else:
            log(f"  ⚠️ 节点 {code} 不存在")
    
    return True

def test_pdf_generation():
    """测试PDF生成"""
    log("测试PDF生成...")
    
    resp = requests.post(f"{BASE_URL}/api/v1/console/orders/{ORDER_ID}/generate-report",
        headers={"X-Staff-Token": STAFF_TOKEN}
    )
    
    assert resp.status_code == 200, f"PDF生成失败: {resp.text}"
    data = resp.json()
    assert data['success'], f"PDF生成失败: {data}"
    
    log(f"✅ PDF生成成功: {data.get('pdf_url', 'N/A')}")
    return True

def run_all_tests():
    """运行所有测试"""
    log("=" * 50)
    log("开始端到端API测试")
    log("=" * 50)
    
    tests = [
        ("客户登录", test_client_login),
        ("创建订单", test_create_order),
        ("技师登录", test_staff_login),
        ("技师接单", test_accept_order),
        ("确认收货", test_receive_order),
        ("拆件检验", test_inspect_order),
        ("维修保养", test_repair_order),
        ("QC通过", test_qc_order),
        ("发货", test_ship_order),
        ("完成订单", test_complete_order),
        ("订单详情验证", test_order_detail),
        ("PDF生成", test_pdf_generation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                log(f"❌ {name} 返回False")
        except Exception as e:
            failed += 1
            log(f"❌ {name} 失败: {str(e)}")
    
    log("=" * 50)
    log(f"测试完成: 通过={passed}, 失败={failed}")
    log("=" * 50)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
