# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
import datetime
import io
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment

class StockDistribution(Document):
    
    def validate(self):
        total_predict = 0
        if self.outlet_selection_table:
            for x in self.outlet_selection_table:
                if x.get("percentage"):
                    total_predict += x.get("percentage")
        if total_predict != 100:
            frappe.throw("Outlet Prediction total must be 100")

# Fetch Purchase Order Items
@frappe.whitelist()
def get_purchase_order_items(po_number):
    purchase_order = frappe.get_doc("Purchase Order", po_number)
    items = []
    
    for item in purchase_order.items:
        items.append({
            'item_code': item.item_code,
            'item_name': item.item_name,
            'qty': item.qty,
            'rate': item.rate
        })
    
    return items

@frappe.whitelist()
def distribution_excell_generate(doc):
    if not doc: doc = {}
    try:
        doc = json.loads(doc)
    except:
        pass
    
    data = []
    columns = get_columns(doc)
    for item in doc.get("purchase_distribution_items"):
        for percentage in doc.get("outlet_selection_table"):
            data_dict = {}
            data_dict["item_code"] = item.get("item_code")
            warehouse = percentage.get("warehouse").lower().replace(" ","_").replace("-","_")
            percentage = percentage.get("percentage")
            data_dict[warehouse] = (float(percentage) / 100) * float(item.get("qty"))
            data.append(data_dict)
    
    file_name = 'stock_distribution.xlsx'
    generate_excel_and_download(columns, data, file_name, height=20)
    
    return "Ok"
    
        
def get_columns(doc):
    columns =  [
        {'fieldname': 'item_code', 'label': 'Item Code', 'expwidth': 13, 'width': 90},
    ]
    for warehouse in doc.get("outlet_selection_table"):
        label = warehouse.get("warehouse").split("-")[0]
        filedname = warehouse.get("warehouse").lower().replace(" ","_").replace("-","_")
        columns.append({"fieldname": filedname, 'label': label, "expwidth": 13, "width": 90})
        
    return columns
    
    
def generate_excel_and_download(columns, data, file_name, height=25):
    fields, labels, row_widths= [], [], []

    for field in columns:
        if field.get('export', True):
            fields.append(field.get('fieldname'))
            labels.append(field.get('label'))
            row_widths.append(field.get('expwidth', 15))

    workbook = openpyxl.Workbook()
    worksheet = workbook.active

    generate_row(worksheet, 1, labels, height=20)
    row_count = 2

    for row in data:
        row_data = [row.get(field) for field in fields]
        generate_row(worksheet, row_count, row_data, widths=row_widths, height=height)
        row_count += 1

    byte_data = io.BytesIO()
    workbook.save(byte_data)

    frappe.local.response.filename = file_name
    frappe.local.response.filecontent = byte_data.getvalue()
    frappe.local.response.type = "download"
    return frappe.local.response


def generate_row(ws, row_count, column_values, font=None, font_size=None, color=None, height=25, widths=None):
    cells = []

    for i, value in enumerate(column_values):
        column_number = i + 1
        cell = ws.cell(row=row_count, column=column_number)
        cell.value = value

        if font:
            cell.font = font
        elif font_size:
            cell.font = Font(size=font_size)

        if color:
            cell.fill = PatternFill(fgColor=color, fill_type='solid')
        if widths:
            ws.column_dimensions[get_column_letter(i + 1)].width = widths[i]

        if isinstance(value, int):
            cell.number_format = "#,##0"
        elif isinstance(value, float):
            cell.number_format = "#,##0.00"

        cell.alignment = Alignment(vertical='center')
        cells.append(cell)

    if height:
        ws.row_dimensions[row_count].height = height

    return cells