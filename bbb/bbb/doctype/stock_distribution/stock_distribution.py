# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
import json
from frappe.model.document import Document
import os
import io
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, PatternFill, Alignment
import random
import string

class StockDistribution(Document):
    
    def validate(self):
        total_predict = 0
        if self.outlet_selection_table:
            for x in self.outlet_selection_table:
                if x.get("percentage"):
                    total_predict += x.get("percentage")
        if total_predict != 100:
            frappe.throw("Outlet Prediction total must be 100")
    
    def on_submit(self):
        if self.upload_distribution_excell and self.against_purchase_receipt:
            # File Path
            excel_file_path = get_site_directory_path() + self.upload_distribution_excell
            
            # Structure Excell Data
            excell_dict = {}
            excell_item_list = []
            grand_total = 0
            message = ""
            excell_data = []
            workbook = openpyxl.load_workbook(excel_file_path, data_only=True)
            sheet = workbook.active
            labels = [cell.value for cell in sheet[1]]
            for row in sheet.iter_rows(min_row=2, values_only=True):
                item_code = "{}".format(row[0])
                excell_item_list.append(item_code)
                total = 0
                row_data = {}
                for x in row[1:]:
                    total += x
                    grand_total += x
                for i, value in enumerate(row):
                    label = labels[i]
                    row_data[label] = value
                excell_data.append(row_data)
                excell_dict[item_code] = total
                
            purchase_receipt = frappe.get_doc("Purchase Receipt",self.against_purchase_receipt)
            if purchase_receipt.items:
                for item in purchase_receipt.items:
                    if item.get("item_code") in excell_item_list:
                        excell_qty = excell_dict.get(item.get("item_code"))
                        pr_qty = item.get("qty")
                        if excell_qty != pr_qty:
                            remain = excell_qty - pr_qty
                            single_message = "Quantity Isn't Equal For Item {item} need {qt_y} \n, ".format(item=item.get("item_code"),qt_y = remain)
                            message += single_message
                    else:
                        frappe.throw("Item {} Isn't Available In Distribution Excell".format(item.get("item_code")))
                        
            if grand_total != purchase_receipt.total_qty:
                frappe.throw(message)
                
            self.create_stock_transfer(purchase_receipt,excell_data)
        else:
            frappe.throw("Please Upload Distribution excell And Set Against Purchase Receipt")
                
    def create_stock_transfer(self,purchase_receipt,excell_data):
        if purchase_receipt.items and excell_data:
            company = purchase_receipt.company
            items = []
            for item in purchase_receipt.items:
                for outlet in excell_data:
                    if item.get("item_code") == str(outlet.get("Item Code")):
                        for key,value in outlet.items():
                            if key != "Item Code":
                                final = ""
                                warehouse = key.lower().replace("_"," ").replace("&","-").title()
                                up = warehouse.split("-")
                                final += up[0]
                                final += "-"
                                final += up[1].upper()
                                data_dict = {}
                                data_dict["item_code"] = item.get("item_code")
                                data_dict["qty"] = value
                                data_dict["s_warehouse"] = item.get("warehouse")
                                data_dict["t_warehouse"] = final
                                data_dict["uom"] = item.get("uom")
                                data_dict["reference_purchase_receipt"] = purchase_receipt.name
                                items.append(data_dict)
            
            stock_entry = frappe.get_doc({
                "doctype": "Stock Entry",
                "stock_entry_type": "Material Transfer",  # You can set the purpose as per your use case
                "company": company,  # Replace with the actual company name
                "items": items
            })
            stock_entry.save(ignore_permissions=True)

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
def get_outlet_items(template):
    temp = frappe.get_doc("Outlet Template", template)
    items = []
    
    for item in temp.outlets:
        items.append({
            'warehouse': item.warehouse,
            'percentage': item.percentage
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
        data_dict = {}
        single_data = {}
        total_wr_wise = 0
        data_dict["item_code"] = item.get("item_code")
        max_percentage = -1  # Assuming all percentages are non-negative
        warehouse_with_max_percentage = None
        
        # loop throw outlet percentage
        for percentage in doc.get("outlet_selection_table"):
            warehouse = percentage.get("warehouse").lower().replace(" ","_").replace("-","&")
            out_percentage = percentage.get("percentage")
            round_am = round((float(out_percentage) / 100) * float(item.get("qty")))
            single_data[warehouse] = round_am
            total_wr_wise += round_am
            
            # get max percentage warehouse
            if percentage.get("percentage") > max_percentage:
                max_percentage = percentage.get("percentage")
                warehouse_with_max_percentage = percentage.get("warehouse")
        
        
        for key,value in single_data.items():
            data_dict[key] = value
            
        if total_wr_wise != item.get("qty"):
            diff = item.get("qty") - total_wr_wise
            max_percentage_warehouse = warehouse_with_max_percentage.lower().replace(" ","_").replace("-","&")
            max_percentage_warehouse_value = data_dict.get(max_percentage_warehouse) + diff
            data_dict[max_percentage_warehouse] = max_percentage_warehouse_value
        
        data.append(data_dict)
        
    name = "distribute-"
    if doc.get("purchase_order"):
        name += doc.get("purchase_order")
    else:
        random_word = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
        name += random_word
    file_name = '{}.xlsx'.format(name)
    generate_excel_and_download(columns, data, file_name, height=20)
    
    return "Ok"
    
        
def get_columns(doc):
    columns =  [
        {'fieldname': 'item_code', 'label': 'Item Code', 'expwidth': 13, 'width': 90},
    ]
    for warehouse in doc.get("outlet_selection_table"):
        label = warehouse.get("warehouse").lower().replace(" ","_").replace("-","&")
        filedname = warehouse.get("warehouse").lower().replace(" ","_").replace("-","&")
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

def get_site_directory_path():
    site_name = frappe.local.site
    cur_dir = os.getcwd()
    return os.path.join(cur_dir, site_name)
    
@frappe.whitelist()
def get_purchase_receipt(purchase_order):
    receipt = frappe.db.sql("""select pr.name from `tabPurchase Receipt Item` as pri 
                                left join `tabPurchase Receipt` as pr on pri.parent = pr.name 
                                    where pri.purchase_order = '{}' group by pr.name""".format(purchase_order))
    if receipt and len(receipt) <= 1:
        return receipt[0][0]
    