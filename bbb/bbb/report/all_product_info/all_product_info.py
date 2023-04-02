# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_item_data(filters)
    return columns, data


def get_conditions(filters):
    conditions = []

    if filters.get("company", None):
        conditions.append("item.company = '%s'" % filters.get("company"))

    conditions.append("item.disabled = 0")
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Product Code"), "fieldname": "product_code", "fieldtype": "Link", "width": 150, "options": "Item"},
        {"label": _("Barcode"), "fieldname": "barcode", "fieldtype": "Link", "width": 150, "options": "Item Barcode"},
        {"label": _("Product Name"), "fieldname": "product_name", "fieldtype": "Text", "width": 450},
        {"label": _("Category Name"), "fieldname": "category", "fieldtype": "Link", "width": 130,
         "options": "Item Group"},
        {"label": _("Sub Category"), "fieldname": "sub_category", "fieldtype": "Link", "width": 130,
         "options": "Item Group"},
        {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 120},
        {"label": _("Buying Price"), "fieldname": "buying_price", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Selling Price"), "fieldname": "selling_price", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_item_data(filters):
    conditions = get_conditions(filters)
    query = """select row_number() over (order by item.name) as serial_no, item.item_code as product_code, item.item_name as product_name, item.item_group as sub_category, item.brand,
     item_group.parent_item_group as category, item.buying_rate as buying_price, item.standard_rate as selling_price,
      item_barcode.barcode from `tabItem` item join `tabItem Group` item_group on item_group.name=item.item_group left join
     `tabItem Barcode` item_barcode on item_barcode.parent=item.name where %s""" % conditions

    query_result = frappe.db.sql(query, as_dict=True)

    return query_result
