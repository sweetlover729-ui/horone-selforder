# -*- coding: utf-8 -*-
"""
PDF生成模块 - 专业维修报告（ReportLab）
Horone@Maintenance 报告书标准版
"""
import os
import re
from logging_config import get_logger

logger = get_logger('pdf_generator')

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                  TableStyle, Image, PageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus.flowables import Flowable
from datetime import datetime
import json
import shutil

# ─── 字体注册 ───────────────────────────────────────────────
FONT_CN  = 'SimHei'   # 中文黑体
FONT_LIGHT = 'SimSun'  # 苹果简宋

try:
    pdfmetrics.registerFont(TTFont(FONT_CN,    '/System/Library/Fonts/STHeiti Light.ttc'))
    pdfmetrics.registerFont(TTFont(FONT_LIGHT, '/System/Library/Fonts/Supplemental/Songti.ttc'))  # pragma: no cover
except Exception:  # pragma: no cover — macOS 字体始终存在
    try:
        pdfmetrics.registerFont(TTFont(FONT_CN,    '/Library/Fonts/Arial Unicode.ttf'))
        pdfmetrics.registerFont(TTFont(FONT_LIGHT, '/Library/Fonts/Arial Unicode.ttf'))
    except Exception:  # pragma: no cover
        FONT_CN    = 'Helvetica'
        FONT_LIGHT = 'Helvetica'

import database as _db_cfg

PDF_DIR = os.environ.get('HORONE_PDF_DIR', os.path.join(_db_cfg.UPLOAD_DIR, 'pdfs'))
BASE_UPLOAD = os.environ.get('HORONE_ORDER_UPLOAD_DIR', _db_cfg.ORDER_UPLOAD_DIR)

WATERMARK_TEXT = "仅供Horone@Maintenance报告书使用"


# ─── 水印 Flowable ─────────────────────────────────────────
class DiagonalWatermark(Flowable):
    """45°对角线水印"""
    def __init__(self, text, width, height):
        Flowable.__init__(self)
        self.text    = text
        self.width   = width
        self.height  = height

    def draw(self):
        self.canv.saveState()
        self.canv.setFont(FONT_CN, 14)
        self.canv.setFillColor(colors.HexColor('#cccccc'))
        self.canv.translate(self.width / 2, self.height / 2)
        self.canv.rotate(45)
        self.canv.drawCentredString(0, 0, self.text)
        self.canv.restoreState()


def ensure_pdf_dir():
    os.makedirs(PDF_DIR, exist_ok=True)


def _photo_path(order_id, node_id, filename):
    """根据文件名或相对路径返回照片的绝对路径。
    支持两种格式:
      - 纯文件名: '外包装1.jpg' → BASE_UPLOAD/order_id/nodes/node_id/外包装1.jpg
      - 相对路径: 'orders/96/nodes/416/外包装1.jpg' → BASE_UPLOAD/../orders/96/nodes/416/外包装1.jpg
    """
    # 如果包含路径分隔符，说明是完整相对路径（如 orders/96/nodes/416/xxx.jpg）
    if '/' in filename:
        full = os.path.join(os.path.dirname(BASE_UPLOAD), filename)
        return full if os.path.exists(full) else None
    p = os.path.join(BASE_UPLOAD, str(order_id), 'nodes', str(node_id), filename)
    return p if os.path.exists(p) else None


def _build_styles():
    styles = getSampleStyleSheet()

    def style(name, **kw):
        base = kw.pop('parent', styles['Normal'])
        return ParagraphStyle(name, parent=base, **kw)

    return {
        'title_main': style('TitleMain',
            fontName=FONT_CN, fontSize=20, alignment=TA_CENTER,
            leading=28, spaceAfter=14, textColor=colors.HexColor('#1a3a6c')),

        'title_sub': style('TitleSub',
            fontName=FONT_LIGHT, fontSize=11, alignment=TA_CENTER,
            leading=16, spaceBefore=6, spaceAfter=20, textColor=colors.HexColor('#1a3a6c')),

        'section': style('Section',
            fontName=FONT_CN, fontSize=11, spaceBefore=10, spaceAfter=4,
            textColor=colors.HexColor('#1a3a6c'),
            borderColor=colors.HexColor('#1a3a6c'), borderWidth=0.5,
            borderPadding=3),

        'field_key': style('FieldKey',
            fontName=FONT_CN, fontSize=9, textColor=colors.HexColor('#555555')),

        'field_val': style('FieldVal',
            fontName=FONT_CN, fontSize=9, textColor=colors.black),

        'node_title': style('NodeTitle',
            fontName=FONT_CN, fontSize=10, spaceBefore=6, spaceAfter=2,
            textColor=colors.HexColor('#1a3a6c')),

        'node_desc': style('NodeDesc',
            fontName=FONT_LIGHT, fontSize=9, spaceAfter=2,
            textColor=colors.HexColor('#333333'), leading=13),

        'node_meta': style('NodeMeta',
            fontName=FONT_LIGHT, fontSize=8,
            textColor=colors.HexColor('#888888')),

        'footer': style('Footer',
            fontName=FONT_LIGHT, fontSize=7.5,
            textColor=colors.HexColor('#aaaaaa'), alignment=TA_CENTER),

        'water': style('Water',
            fontName=FONT_CN, fontSize=8, alignment=TA_CENTER,
            textColor=colors.HexColor('#bbbbbb')),
    }


def _t(text, en=''):
    """双语格式"""
    if en:
        return f"{text} — {en}"
    return text


def _make_table(data, col_widths, header_bg='#1a3a6c', fontsize=9):
    t = Table(data, colWidths=col_widths)
    rows = len(data)
    t.setStyle(TableStyle([
        ('FONTNAME',     (0,0), (-1,-1), FONT_CN),
        ('FONTSIZE',     (0,0), (-1,-1), fontsize),
        ('BACKGROUND',   (0,0), (-1,0),  colors.HexColor(header_bg)),
        ('TEXTCOLOR',   (0,0), (-1,0),  colors.white),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('GRID',         (0,0), (-1,-1), 0.4, colors.HexColor('#dddddd')),
        ('TOPPADDING',   (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LEFTPADDING',  (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1),
         [colors.white, colors.HexColor('#f5f8fc')]),
    ]))
    return t


def _photo_cell(photo_list, order_id, node_id, max_w=6.5*cm, max_h=5*cm):
    """返回照片Image对象列表（带占位符）"""
    cells = []
    for fname in photo_list[:2]:  # 最多2张
        p = _photo_path(order_id, node_id, fname)
        if p:
            try:
                img = Image(p, width=max_w, height=max_h)
                img.hAlign = 'CENTER'
                cells.append(img)
            except Exception:  # pragma: no cover
                cells.append(Paragraph('📷', ParagraphStyle('ph', fontName=FONT_CN, fontSize=20,  # pragma: no cover
                                                            alignment=TA_CENTER)))
        else:
            cells.append(Paragraph('📷', ParagraphStyle('ph', fontName=FONT_CN, fontSize=20,
                                                        alignment=TA_CENTER)))
    # 补齐2格
    while len(cells) < 2:
        cells.append(Paragraph('', ParagraphStyle('ph')))
    return cells


def _fmt_time(v):
    """标准化时间格式为 YYYY-MM-DD HH:MM:SS"""
    if not v:
        return ''
    s = str(v)
    # 去掉毫秒 .123456
    s = re.sub(r'\.[0-9]+', '', s)
    # 去掉时区后缀如 GMT、+08:00 等
    s = re.sub(r'\s+[A-Z]{2,4}$', '', s)
    s = re.sub(r'\+[0-9]{2}:[0-9]{2}$', '', s)
    s = s.strip()
    # 已经是标准格式则直接返回
    if re.match(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', s):
        return s
    # 从带星期格式提取："Wed, 01 Apr 2026 16:56:35"
    m = re.search(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}:\d{2}', s)
    if m:
        try:
            from datetime import datetime as _dt
            parsed = _dt.strptime(m.group(0), '%d %b %Y %H:%M:%S')
            return parsed.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:  # pragma: no cover
            pass  # pragma: no cover
    # 处理 "2026-04-24 01:52:49+08:00" 这种无毫秒但带时区的格式
    m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\s*([+-]\d{2}:\d{2})?', s)
    if m:
        return m.group(1) + ' ' + m.group(2)  # pragma: no cover
    # 兜底：提取日期时间部分
    m = re.search(r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})', s)  # pragma: no cover
    if m:  # pragma: no cover
        return m.group(1) + ' ' + m.group(2)  # pragma: no cover
    return s


def _build_cover_page(order_data, conn, S):
    """第1页：综合报告（单页）"""
    story = []
    order_id = order_data['id']

    # 标题区
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("潜水装备检测维修保养综合报告", S['title_main']))
    story.append(Paragraph("SCUBA Equipment Inspection & Maintenance Report", S['title_sub']))
    story.append(Spacer(1, 3*mm))

    # 分隔线
    line_data = [['']]
    line_t = Table(line_data, colWidths=[17*cm], rowHeights=[1.5])
    line_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1a3a6c')),
        ('LINEABOVE', (0,0), (-1,0), 1.5, colors.HexColor('#1a3a6c')),
    ]))
    story.append(line_t)
    story.append(Spacer(1, 6*mm))

    cursor = conn.cursor()

    # ── 订单信息（2x2表格）──
    story.append(Paragraph(_t('订单信息', 'Order Information'), S['section']))

    # 使用 Paragraph 包装，支持自动换行，防止文字溢出
    lbl_s = ParagraphStyle('InfoLbl', fontName=FONT_CN, fontSize=8.5,
        textColor=colors.HexColor('#555555'), alignment=TA_RIGHT, leading=12)
    val_s = ParagraphStyle('InfoVal', fontName=FONT_CN, fontSize=8.5,
        textColor=colors.black, alignment=TA_LEFT, leading=12)

    order_no_val = str(order_data.get('order_no','') or '')
    report_date_val = datetime.now().strftime('%Y-%m-%d')

    created_at_val = _fmt_time(order_data.get('created_at'))
    completed_at_val = _fmt_time(order_data.get('completed_at'))

    info_data = [
        [Paragraph('订单编号', lbl_s), Paragraph(order_no_val, val_s),
         Paragraph('报告日期', lbl_s), Paragraph(report_date_val, val_s)],
        [Paragraph('下单时间', lbl_s), Paragraph(created_at_val, val_s),
         Paragraph('完成时间', lbl_s), Paragraph(completed_at_val, val_s)],
    ]

    # 调整列宽：标签列窄一些（2.8cm），值列宽一些（5.7cm）
    info_t = Table(info_data, colWidths=[2.8*cm, 5.7*cm, 2.8*cm, 5.7*cm])
    info_t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1), FONT_CN), ('FONTSIZE',(0,0),(-1,-1), 8.5),
        ('BACKGROUND',(0,0),(0,-1), colors.HexColor('#eef2f8')),
        ('BACKGROUND',(2,0),(2,-1), colors.HexColor('#eef2f8')),
        ('GRID',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 5*mm))

    # ── 客户信息 ──
    story.append(Paragraph(_t('客户信息', 'Customer Information'), S['section']))
    c_name   = order_data.get('receiver_name', '') or ''
    c_phone  = order_data.get('receiver_phone', '') or ''
    c_addr   = order_data.get('receiver_address', '') or ''

    val_style = ParagraphStyle('Val', fontName=FONT_CN, fontSize=9,
        textColor=colors.black, leading=13)
    lbl_style = ParagraphStyle('Lbl2', fontName=FONT_CN, fontSize=9,
        textColor=colors.HexColor('#555555'), leading=13)

    row1 = [
        Paragraph(_t('客户姓名','Name'), lbl_style),
        Paragraph(c_name or _t('未填写','N/A'), val_style),
        Paragraph(_t('联系电话','Phone'), lbl_style),
        Paragraph(c_phone or _t('未填写','N/A'), val_style),
    ]
    row2 = [
        Paragraph(_t('收件地址','Address'), lbl_style),
        Paragraph(c_addr or _t('未填写','N/A'), val_style),
        '', '',
    ]

    c_t = Table([row1, row2], colWidths=[2.2*cm, 5.3*cm, 2.2*cm, 6.8*cm])
    c_t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1), FONT_CN), ('FONTSIZE',(0,0),(-1,-1), 9),
        ('BACKGROUND',(0,0),(-1,-1), colors.HexColor('#f8fafd')),
        ('BOX',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
        ('INNERGRID',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
        ('ALIGN',(0,0),(0,-1),'RIGHT'), ('ALIGN',(2,0),(2,-1),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('SPAN',(1,1),(3,1)),
    ]))
    story.append(c_t)
    story.append(Spacer(1, 5*mm))

    # ── 设备信息（四列格式）──
    story.append(Paragraph(_t('设备信息', 'Equipment Information'), S['section']))
    
    # 从数据库读取设备检测数据
    cursor.execute('''
        SELECT oi.id, pt.name as product_type, b.name as brand, m.name as model,
               eid.first_stage_count, eid.first_stage_serials, 
               eid.first_stage_pre_pressure, eid.first_stage_post_pressure,
               eid.second_stage_count, eid.second_stage_serials,
               eid.second_stage_pre_resistance, eid.second_stage_post_resistance
        FROM order_items oi
        LEFT JOIN product_types pt ON oi.product_type_id = pt.id
        LEFT JOIN brands b ON oi.brand_id = b.id
        LEFT JOIN models m ON oi.model_id = m.id
        LEFT JOIN equipment_inspection_data eid ON oi.id = eid.order_item_id
        WHERE oi.order_id = %s
    ''', (order_id,))
    equipment_items = cursor.fetchall()
    
    if equipment_items:
        for idx, item in enumerate(equipment_items, 1):
            # 设备标题
            device_name = f"{item['brand'] or '未知品牌'} {item['model'] or '未知型号'}"
            story.append(Paragraph(f"设备 #{idx}: {device_name}", ParagraphStyle('DeviceTitle',
                fontName=FONT_CN, fontSize=10, textColor=colors.HexColor('#1a3a6c'),
                spaceBefore=8, spaceAfter=4)))
            
            # 一级头数据
            fs_count = item['first_stage_count'] or 0
            if fs_count > 0:
                fs_serials = item['first_stage_serials'] or []
                fs_pre = item['first_stage_pre_pressure'] or []
                fs_post = item['first_stage_post_pressure'] or []
                
                fs_data = [['一级头', '序列号', '保养前气瓶压力10-150Bar\n时中压范围(Bar)', '保养后气瓶压力10-150Bar\n时中压范围(Bar)']]
                for i in range(fs_count):
                    fs_data.append([
                        f'#{i+1}',
                        fs_serials[i] if i < len(fs_serials) else '-',
                        str(fs_pre[i]) if i < len(fs_pre) and fs_pre[i] else '-',
                        str(fs_post[i]) if i < len(fs_post) and fs_post[i] else '-'
                    ])
                
                fs_t = Table(fs_data, colWidths=[2*cm, 4*cm, 4.5*cm, 4.5*cm])
                fs_t.setStyle(TableStyle([
                    ('FONTNAME',(0,0),(-1,-1), FONT_CN), ('FONTSIZE',(0,0),(-1,-1), 8),
                    ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#eef2f8')),
                    ('BACKGROUND',(0,1),(0,-1), colors.HexColor('#f8fafd')),
                    ('GRID',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
                    ('ALIGN',(0,0),(0,-1),'LEFT'),
                    ('ALIGN',(1,0),(-1,-1),'CENTER'),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
                    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                ]))
                story.append(fs_t)
                story.append(Spacer(1, 3*mm))
            
            # 二级头数据
            ss_count = item['second_stage_count'] or 0
            if ss_count > 0:
                ss_serials = item['second_stage_serials'] or []
                ss_pre = item['second_stage_pre_resistance'] or []
                ss_post = item['second_stage_post_resistance'] or []
                
                ss_data = [['二级头', '序列号', '保养前抗阻(cmH2O)', '保养后抗阻(cmH2O)']]
                for i in range(ss_count):
                    ss_data.append([
                        f'#{i+1}',
                        ss_serials[i] if i < len(ss_serials) else '-',
                        str(ss_pre[i]) if i < len(ss_pre) and ss_pre[i] else '-',
                        str(ss_post[i]) if i < len(ss_post) and ss_post[i] else '-'
                    ])
                
                ss_t = Table(ss_data, colWidths=[2.5*cm, 5*cm, 4*cm, 4*cm])
                ss_t.setStyle(TableStyle([
                    ('FONTNAME',(0,0),(-1,-1), FONT_CN), ('FONTSIZE',(0,0),(-1,-1), 8),
                    ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#eef2f8')),
                    ('BACKGROUND',(0,1),(0,-1), colors.HexColor('#f8fafd')),
                    ('GRID',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
                    ('ALIGN',(0,0),(0,-1),'LEFT'),
                    ('ALIGN',(1,0),(-1,-1),'CENTER'),
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                    ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
                    ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                ]))
                story.append(ss_t)
                story.append(Spacer(1, 3*mm))
    else:
        # 无数据时显示占位
        eq_data = [
            ['调节器一级头', '序列号', '保养前气瓶压力10-150Bar\n时中压范围(Bar)', '保养后气瓶压力10-150Bar\n时中压范围(Bar)'],
            ['二级头', '序列号', '保养前抗阻', '保养后抗阻'],
        ]
        eq_t = Table(eq_data, colWidths=[3.5*cm, 4*cm, 4.25*cm, 4.25*cm])
        eq_t.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1), FONT_CN), ('FONTSIZE',(0,0),(-1,-1), 9),
            ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#eef2f8')),
            ('BACKGROUND',(0,1),(0,1), colors.HexColor('#eef2f8')),
            ('GRID',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
            ('ALIGN',(0,0),(0,-1),'LEFT'),
            ('ALIGN',(1,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ]))
        story.append(eq_t)
    
    # ── 专项服务（仅当管理员添加了专项服务时显示）──
    cursor.execute('''
        SELECT name, description, quantity, staff_note FROM special_service_records
        WHERE order_id = %s
    ''', (order_id,))
    special_records = cursor.fetchall()
    if special_records:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph('专项服务', ParagraphStyle('SpecialTitle',
            fontName=FONT_CN, fontSize=10, textColor=colors.HexColor('#1a3a6c'),
            spaceBefore=6, spaceAfter=4)))
        for sr in special_records:
            line = sr['name'] or ''
            if sr.get('quantity') and sr['quantity'] > 1:
                line += f" x{sr['quantity']}"
            if sr.get('description'):
                line += f" — {sr['description']}"
            story.append(Paragraph(f"· {line}", ParagraphStyle('SpecialItem',
                fontName=FONT_LIGHT, fontSize=9, textColor=colors.HexColor('#333333'),
                leftIndent=12, spaceAfter=2)))
            if sr.get('staff_note'):
                story.append(Paragraph(f"  备注：{sr['staff_note']}", ParagraphStyle('SpecialNote',
                    fontName=FONT_LIGHT, fontSize=8, textColor=colors.HexColor('#666666'),
                    leftIndent=24, spaceAfter=2)))
    
    story.append(Spacer(1, 5*mm))

    # ── 确认签字（原费用明细位置）──
    story.append(Paragraph(_t('确认签字', 'Signatures & Confirmation'), S['section']))
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 获取维修员姓名
    tech_name = ''
    cursor.execute('''
        SELECT staff_name FROM tracking_nodes
        WHERE order_id = %s AND node_code IN ('repair', 'inspect', 'qc')
        ORDER BY created_at ASC LIMIT 1
    ''', (order_id,))
    row = cursor.fetchone()
    if row and row['staff_name']:
        tech_name = row['staff_name']
    
    qc_name = '皓壹潜水中心QC部'

    sig_data = [
        [_t('签字方','Party'), _t('签字人','Signer'), _t('日期','Date'), _t('备注','Note')],
        [_t('维修员','Technician'), tech_name or '____________________', today, ''],
        [_t('质检员','QC Inspector'), qc_name, today, ''],
        [_t('客户','Customer'),      '____________________', '____________', ''],
    ]
    sig_t = Table(sig_data, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    sig_t.setStyle(TableStyle([
        ('FONTNAME',(0,0),(-1,-1), FONT_CN), ('FONTSIZE',(0,0),(-1,-1), 9),
        ('BACKGROUND',(0,0),(-1,0), colors.HexColor('#1a3a6c')),
        ('TEXTCOLOR',(0,0),(-1,0), colors.white),
        ('GRID',(0,0),(-1,-1), 0.4, colors.HexColor('#cccccc')),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(sig_t)
    story.append(Spacer(1, 8*mm))

    # 维修声明
    declare = (
        "本报告由皓壹调节器维修保养服务平台自动生成，维修项目参照出厂标准执行。"
        "如对报告内容有异议，请在收到报告后7天内联系客服处理。"
    )
    story.append(Paragraph(declare, ParagraphStyle('Declare',
        fontName=FONT_LIGHT, fontSize=8, textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER, leading=12)))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "This report is auto-generated by Horone Maintenance Platform. "
        "Contact us within 7 days if you have any concerns.",
        ParagraphStyle('DeclareEn', fontName=FONT_LIGHT, fontSize=7.5,
                      textColor=colors.HexColor('#888888'), alignment=TA_CENTER)))

    return story


def _build_process_page(order_data, conn, S):
    """第2-N页：全流程节点记录（动态图片布局，去重）"""
    story = []
    order_id = order_data['id']
    cursor = conn.cursor()

    # 标题
    story.append(Paragraph("全流程节点记录", S['title_main']))
    story.append(Paragraph("Complete Process Records", ParagraphStyle('TitleEn',
        fontName=FONT_LIGHT, fontSize=12, leading=18, alignment=TA_CENTER,
        spaceAfter=16, textColor=colors.HexColor('#1a3a6c'))))
    story.append(Spacer(1, 3*mm))
    line_t = Table([['']], colWidths=[17*cm], rowHeights=[1])
    line_t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), colors.HexColor('#1a3a6c'))]))
    story.append(line_t)
    story.append(Spacer(1, 5*mm))

    # 定义固定的流程步骤顺序和标准名称
    PROCESS_STEPS = [
        ('created',   '订单确认',     'Order Confirmed'),
        ('received',  '确认收货',     'Item Received'),
        ('inspect',   '拆件检验',     'Inspection'),
        ('repair',    '维修保养',     'Maintenance'),
        ('qc',        '质检通过',     'QC Passed'),
        ('shipped',   '回寄客户',     'Shipped to Customer'),
        ('completed', '订单完成',     'Completed'),
    ]
    # node_code → 步骤序号映射
    step_order = {s[0]: i for i, s in enumerate(PROCESS_STEPS)}
    # node_code → 标准中文名称
    step_name_cn = {s[0]: s[1] for s in PROCESS_STEPS}
    # 兼容历史数据：paid 是 created 的旧 node_code
    step_name_cn['paid'] = '订单确认'
    step_order['paid'] = step_order.get('created', 0)

    # 取所有节点，保留所有历史记录（不去重）
    cursor.execute('''
        SELECT id, node_code, node_name, description, operate_time,
            staff_name, operate_note, photos, created_at
        FROM tracking_nodes
        WHERE order_id = %s
        ORDER BY created_at ASC
    ''', (order_id,))
    all_nodes = cursor.fetchall()
    
    # paid 与 created 是同一步骤，只保留 created（过滤 paid）
    has_created = any(n['node_code'] == 'created' for n in all_nodes)
    if has_created:
        all_nodes = [n for n in all_nodes if n['node_code'] != 'paid']

    # 按固定流程顺序排序，确保步骤顺序始终正确
    nodes = sorted(all_nodes, key=lambda x: (step_order.get(x['node_code'], 99), x['created_at']))

    if not nodes:
        story.append(Paragraph(_t('暂无流程记录', 'No process records yet'), S['field_val']))
        return story

    for idx, node in enumerate(nodes, 1):
        try:
            photos = json.loads(node['photos']) if node['photos'] else []
        except Exception:
            photos = []

        node_code = node['node_code'] or ''

        # ── 步骤标题 ──
        # 使用标准中文名称，而非数据库中可能不一致的 node_name
        display_name = step_name_cn.get(node_code, node['node_name'] or node_code)
        node_title_style = ParagraphStyle('nt', fontName=FONT_CN, fontSize=11,
            textColor=colors.HexColor('#1a3a6c'), spaceBefore=4, spaceAfter=2)
        story.append(Paragraph(f"第{idx}步 · {display_name}", node_title_style))

        # ── 操作信息 ──
        meta_parts = []
        if node['operate_time']:
            ot = node['operate_time']
            # 处理 datetime 对象：转为字符串
            if hasattr(ot, 'strftime'):
                ot = ot.strftime('%Y-%m-%d %H:%M:%S')
            meta_parts.append(str(ot))
        if node['staff_name']:
            meta_parts.append(str(node['staff_name']))
        if meta_parts:
            meta_style = ParagraphStyle('nm', fontName=FONT_LIGHT, fontSize=8,
                textColor=colors.HexColor('#888888'), spaceAfter=2)
            story.append(Paragraph(' | '.join(meta_parts), meta_style))

        # ── 描述/备注 ──
        desc_text = (node['description'] or '') + ('<br/>' + node['operate_note'] if node['operate_note'] else '')
        if desc_text.strip():
            desc_style = ParagraphStyle('nd', fontName=FONT_LIGHT, fontSize=9,
                textColor=colors.HexColor('#333333'), leading=12, spaceAfter=3)
            story.append(Paragraph(desc_text, desc_style))

        # ── 照片区域 ──
        if photos and len(photos) > 0:
            PHOTOS_PER_ROW = 3
            PHOTO_W = 5.0 * cm
            PHOTO_H = 3.75 * cm
            rows = []
            current_row = []
            for fname in photos:
                # 兼容新旧照片格式
                if isinstance(fname, dict):
                    fname = fname.get('path', '')  # pragma: no cover
                if not fname:
                    continue  # pragma: no cover
                p = _photo_path(order_id, node['id'], fname)
                if p:
                    try:  # pragma: no cover
                        img = Image(p, width=PHOTO_W, height=PHOTO_H)  # pragma: no cover
                        img.hAlign = 'CENTER'  # pragma: no cover
                        current_row.append(img)  # pragma: no cover
                    except Exception:  # pragma: no cover
                        pass  # pragma: no cover
                if len(current_row) == PHOTOS_PER_ROW:
                    rows.append(current_row)  # pragma: no cover
                    current_row = []  # pragma: no cover
            if current_row:
                while len(current_row) < PHOTOS_PER_ROW:  # pragma: no cover
                    current_row.append(Paragraph('', ParagraphStyle('ph')))  # pragma: no cover
                rows.append(current_row)  # pragma: no cover

            if rows:
                col_widths = [PHOTO_W + 0.3*cm] * PHOTOS_PER_ROW  # pragma: no cover
                photo_grid = Table(rows, colWidths=col_widths)  # pragma: no cover
                photo_grid.setStyle(TableStyle([  # pragma: no cover
                    ('ALIGN',(0,0),(-1,-1),'CENTER'),  # pragma: no cover
                    ('VALIGN',(0,0),(-1,-1),'MIDDLE'),  # pragma: no cover
                    ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#cccccc')),  # pragma: no cover
                    ('TOPPADDING',(0,0),(-1,-1),2),  # pragma: no cover
                    ('BOTTOMPADDING',(0,0),(-1,-1),2),  # pragma: no cover
                    ('SPLITBYROW',(0,0),(-1,-1)),  # pragma: no cover
                ]))  # pragma: no cover
                photo_grid.splitByRow = True  # pragma: no cover
                story.append(photo_grid)  # pragma: no cover

        # 分隔线
        story.append(Spacer(1, 2*mm))
        sep_t = Table([['']], colWidths=[17*cm], rowHeights=[0.5])
        sep_t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1), colors.HexColor('#e0e8f0'))]))
        story.append(sep_t)
        story.append(Spacer(1, 2*mm))

    return story


def _page_template(canvas, doc):
    """页眉页脚回调"""
    canvas.saveState()
    w, h = A4
    # 页眉
    canvas.setFont(FONT_CN, 8)
    canvas.setFillColor(colors.HexColor('#1a3a6c'))
    canvas.drawString(2*cm, h - 1.2*cm, "Horone@Maintenance · 潜水装备维修报告")
    canvas.setFillColor(colors.HexColor('#aaaaaa'))
    canvas.drawRightString(w - 2*cm, h - 1.2*cm,
                           f"第{doc.page}页 / {datetime.now().strftime('%Y-%m-%d')}")
    # 页脚线
    canvas.setStrokeColor(colors.HexColor('#dddddd'))
    canvas.line(2*cm, 1.5*cm, w - 2*cm, 1.5*cm)
    canvas.restoreState()


def generate_order_pdf(order_data, _db_conn=None, staff_name=''):
    """
    生成专业维修报告 PDF
    注意: 仅生成PDF文件，返回路径，由调用方更新数据库
    """
    ensure_pdf_dir()
    order_no = order_data.get('order_no', 'UNKNOWN')
    pdf_path = os.path.join(PDF_DIR, f"{order_no}.pdf")

    # 使用独立连接（只读操作，不会锁）
    import database as _db_module
    local_conn = _db_module.get_connection()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2.2*cm,
        title=f"Horone维修报告_{order_no}",
        author="Horone@Maintenance",
        subject="潜水装备维修保养报告",
    )

    S = _build_styles()
    story = []

    try:
        # 第1页：综合报告
        story.extend(_build_cover_page(order_data, local_conn, S))
        story.append(PageBreak())

        # 第2-N页：全流程节点记录
        story.extend(_build_process_page(order_data, local_conn, S))

        doc.build(story, onFirstPage=_page_template, onLaterPages=_page_template)
    finally:
        local_conn.close()

    return pdf_path


# ─── 归档清理（供 archive-cleanup 调用）────────────────────
def cleanup_expired_pdfs(days=15):
    """清理超过N天的照片文件（PDF文件保留，仅对客户不可见；数据库记录保留）"""
    import time, re
    cutoff = time.time() - days * 86400
    cleaned = 0
    for fname in os.listdir(PDF_DIR):
        fpath = os.path.join(PDF_DIR, fname)
        if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
            cleaned += 1
            m = re.match(r'report_(\d+)', fname)
            if m:
                order_id = m.group(1)
                photos_deleted = cleanup_order_photos(int(order_id))
                if photos_deleted > 0:
                    logger.info("照片清理 order_id=%s, 删除%d张照片(超过%d天)", order_id, photos_deleted, days)
    return cleaned


def cleanup_order_photos(order_id, conn=None):
    """
    清理订单的所有照片文件
    """
    import glob
    order_photo_dir = os.path.join(BASE_UPLOAD, str(order_id))
    if not os.path.exists(order_photo_dir):
        return 0
    
    deleted = 0
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']:
        for fpath in glob.glob(os.path.join(order_photo_dir, '**', ext), recursive=True):
            try:
                os.remove(fpath)
                deleted += 1
            except Exception:
                pass
    
    for root, dirs, files in os.walk(order_photo_dir, topdown=False):
        for d in dirs:
            dir_path = os.path.join(root, d)
            try:
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
            except Exception:
                pass
    
    return deleted


if __name__ == '__main__':  # pragma: no cover — 手动调试入口
    import database
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE status='completed' LIMIT 1")
    row = cursor.fetchone()
    if row:
        path = generate_order_pdf(dict(row), None)
        logger.info("PDF生成: %s", path)
    database.release_connection(conn)
