# -*- coding: utf-8 -*-
"""routes_console/__init__.py — save_base64_image 全分支覆盖"""
import pytest
from unittest.mock import patch, MagicMock
import os
import base64

import routes_console as console_module
from routes_console import save_base64_image


class TestSaveBase64Image:
    """save_base64_image 函数"""

    def test_save_jpeg(self, tmp_path):
        """有效 JPEG → 正常保存"""
        # 1x1 白色 JPEG
        jpeg = (b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01'
                b'\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07'
                b'\x07\x07\x09\x09\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13'
                b'\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c'
                b'(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01'
                b'\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
                b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04'
                b'\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00'
                b'\xd2\xcf \xff\xd9')
        b64 = base64.b64encode(jpeg).decode()

        with patch.object(console_module.database, 'ORDER_UPLOAD_DIR',
                          str(tmp_path / 'uploads')):
            result = save_base64_image(b64, 1)
            assert result is not None
            assert result.startswith('orders/1/nodes/')
            assert result.endswith('.jpg')

    def test_save_jpeg_with_prefix(self, tmp_path):
        """带 data:image/jpeg;base64, 前缀"""
        jpeg = (b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01'
                b'\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07'
                b'\x07\x07\x09\x09\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13'
                b'\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c'
                b'(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01'
                b'\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01'
                b'\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04'
                b'\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00'
                b'\xd2\xcf \xff\xd9')
        b64 = 'data:image/jpeg;base64,' + base64.b64encode(jpeg).decode()

        with patch.object(console_module.database, 'ORDER_UPLOAD_DIR',
                          str(tmp_path / 'uploads')):
            result = save_base64_image(b64, 1, node_id=100)
            assert result is not None
            assert 'nodes/100' in result

    def test_save_png(self, tmp_path):
        """有效 PNG → 正常保存"""
        # 最小 PNG
        png = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
               b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
               b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
               b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        b64 = base64.b64encode(png).decode()

        with patch.object(console_module.database, 'ORDER_UPLOAD_DIR',
                          str(tmp_path / 'uploads')):
            result = save_base64_image(b64, 2)
            assert result is not None
            assert result.endswith('.png')

    def test_invalid_magic_bytes(self, tmp_path):
        """非法文件格式 (前4字节不匹配) → 返回 None"""
        b64 = base64.b64encode(b'DEADBEEFXXXXX').decode()
        with patch.object(console_module.database, 'ORDER_UPLOAD_DIR',
                          str(tmp_path / 'uploads')):
            result = save_base64_image(b64, 1)
            assert result is None

    def test_decode_error(self):
        """无效 Base64 → Exception → 返回 None"""
        result = save_base64_image('not-valid-base64!!!', 1)
        assert result is None
