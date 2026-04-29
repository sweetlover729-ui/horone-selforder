# -*- coding: utf-8 -*-
"""
Pydantic 请求校验模块 — 统一校验层
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ===== 客户端 =====

class CustomerPhoneLogin(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    name: Optional[str] = ''

    @field_validator('phone')
    @classmethod
    def phone_must_be_digits(cls, v):
        if not v.isdigit():
            raise ValueError('手机号必须为11位数字')
        return v


class OrderCreateItem(BaseModel):
    product_type_id: int = Field(..., gt=0)
    brand_id: Optional[int] = None
    model_id: Optional[int] = None
    brand_name: Optional[str] = ''
    model_name: Optional[str] = ''
    service_type_id: int = Field(..., gt=0)
    service_name: Optional[str] = ''
    quantity: int = Field(default=1, ge=1)
    customer_note: Optional[str] = ''


class CreateOrder(BaseModel):
    items: List[OrderCreateItem] = Field(..., min_length=1, max_length=20)
    delivery_type: str = Field(default='store')
    receiver_name: str = Field(default='', max_length=50)
    receiver_phone: str = Field(default='', max_length=20)
    receiver_address: Optional[str] = ''
    urgent_service: bool = False
    customer_note: Optional[str] = ''


class EditOrder(BaseModel):
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    items: Optional[List[dict]] = None


class ExpressUpdate(BaseModel):
    express_company: str = Field(..., min_length=1, max_length=100)
    express_no: str = Field(..., min_length=1, max_length=100)


class SpecialServiceRespond(BaseModel):
    record_id: int = Field(..., gt=0)
    action: str = Field(...)
    paid: bool = False

    @field_validator('action')
    @classmethod
    def action_must_be_valid(cls, v):
        if v not in ('confirm', 'reject'):
            raise ValueError('action 必须为 confirm 或 reject')
        return v


# ===== 管理后台 + 技师端 =====

class StaffLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)


class PriceOverrideCreate(BaseModel):
    product_type_id: int = Field(..., gt=0)
    brand_id: Optional[int] = None
    service_type_id: Optional[int] = None
    model_id: Optional[int] = None
    price: float = Field(..., ge=0)
    category: Optional[str] = ''


class ModelCreate(BaseModel):
    brand_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    category_ids: Optional[List[int]] = []
