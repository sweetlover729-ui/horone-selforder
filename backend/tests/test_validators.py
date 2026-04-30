"""Tests for Pydantic validators"""
import pytest
from validators import (
    CustomerPhoneLogin, OrderCreateItem, CreateOrder,
    EditOrder, ExpressUpdate, SpecialServiceRespond,
    StaffLogin, PriceOverrideCreate, ModelCreate,
)


class TestCustomerPhoneLogin:
    def test_valid_phone(self):
        m = CustomerPhoneLogin(phone='13900000001', name='Test')
        assert m.phone == '13900000001'
        assert m.name == 'Test'
    def test_phone_too_short(self):
        with pytest.raises(Exception):
            CustomerPhoneLogin(phone='12345', name='')
    def test_phone_not_digits(self):
        with pytest.raises(Exception):
            CustomerPhoneLogin(phone='abcdefghijk', name='')
    def test_name_optional(self):
        m = CustomerPhoneLogin(phone='13900000001')
        assert m.name == ''


class TestOrderCreateItem:
    def test_minimal_valid(self):
        m = OrderCreateItem(product_type_id=1, service_type_id=15)
        assert m.product_type_id == 1
        assert m.service_type_id == 15
        assert m.quantity == 1
    def test_with_brand_model(self):
        m = OrderCreateItem(product_type_id=1, brand_id=1, model_id=10, service_type_id=15)
        assert m.brand_id == 1
        assert m.model_id == 10


class TestCreateOrder:
    def test_minimal_valid(self):
        m = CreateOrder(items=[OrderCreateItem(product_type_id=1, service_type_id=15)], receiver_name='Test')
        assert len(m.items) == 1
        assert m.delivery_type == 'store'
    def test_empty_items(self):
        with pytest.raises(Exception):
            CreateOrder(items=[], receiver_name='')
    def test_urgent_service(self):
        m = CreateOrder(items=[OrderCreateItem(product_type_id=1, service_type_id=15)], urgent_service=True)
        assert m.urgent_service is True


class TestEditOrder:
    def test_all_optional(self):
        m = EditOrder()
        assert m.receiver_name is None
        assert m.receiver_phone is None


class TestExpressUpdate:
    def test_valid(self):
        m = ExpressUpdate(express_company='顺丰', express_no='SF123456789')
        assert m.express_company == '顺丰'
    def test_empty_company_fails(self):
        with pytest.raises(Exception):
            ExpressUpdate(express_company='', express_no='123')


class TestSpecialServiceRespond:
    def test_confirm(self):
        m = SpecialServiceRespond(record_id=1, action='confirm', paid=True)
        assert m.action == 'confirm'
        assert m.paid is True
    def test_reject(self):
        m = SpecialServiceRespond(record_id=1, action='reject', paid=False)
        assert m.action == 'reject'
    def test_invalid_action(self):
        with pytest.raises(Exception):
            SpecialServiceRespond(record_id=1, action='invalid', paid=False)


class TestStaffLogin:
    def test_valid(self):
        m = StaffLogin(username='kent', password='LILY1018@kent729')
        assert m.username == 'kent'
    def test_empty_username_fails(self):
        with pytest.raises(Exception):
            StaffLogin(username='', password='pw')


class TestPriceOverrideCreate:
    def test_valid(self):
        m = PriceOverrideCreate(product_type_id=1, price=100.0)
        assert m.price == 100.0


class TestModelCreate:
    def test_valid(self):
        m = ModelCreate(brand_id=1, name='Test Model', category_ids=[1, 2])
        assert m.brand_id == 1
        assert len(m.category_ids) == 2
