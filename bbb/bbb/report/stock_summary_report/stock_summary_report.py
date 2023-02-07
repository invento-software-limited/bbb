# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    if not filters:
        filters = {}
    columns = get_columns()
    stock = get_total_stock(filters, columns)

    return columns, stock


def get_columns():
    columns = [
        # {"label": _("No"), "fieldname": "serial_no", "fieldtype": "Text", "width": 100},
        {"label": _("Product Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item",
         "width": 100},
        {"label": _("Product Name"), "fieldname": "item_name", "fieldtype": "Text", "width": 400},
        # {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand",
        #  "width": 100},
        # {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",
        #  "width": 150},
        {"label": _("Total Quantity"), "fieldname": "actual_qty", "fieldtype": "Float", "width": 120},
        {"label": _("MRP"), "fieldname": "mrp", "fieldtype": "Currency", "width": 160,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Value"), "fieldname": "total_value", "fieldtype": "Currency", "width": 200,
         "convertible": "rate", "options": "currency"},
    ]

    return columns


def get_total_stock(filters, columns):
    conditions = ""
    warehouse_conditions = []
    # if filters.get("group_by") == "Warehouse":
    #     if filters.get("company"):
    #         conditions += " AND warehouse.company = %s" % frappe.db.escape(filters.get("company"), percent=False)
    #
    #     conditions += " GROUP BY ledger.warehouse, item.item_code"
    #     columns += "'' as company, ledger.warehouse"


    if filters.get('all_warehouse'):
        pass
    elif filters.get('warehouse'):
        warehouse_list = filters.get('warehouse')
        for warehouse in warehouse_list:
            warehouse_conditions.append(" ledger.warehouse = '%s'" % warehouse)
            columns.append({"label": _(warehouse), "fieldname": warehouse, "fieldtype": "Int", "width": 120, "options": "Warehouse"},)
    if warehouse_conditions:
        warehouse_conditions = " or ".join(warehouse_conditions)
        warehouse_conditions = ' and (' + warehouse_conditions + ')'
        conditions += warehouse_conditions
    if filters.get('item_group'):
        conditions += " and item.item_group = '%s'" % filters.get('item_group')

    if filters.get('brand'):
        conditions += " and item.brand = '%s'" % filters.get('brand')

    if filters.get("group_by") == "All":
        conditions += " GROUP BY item.item_code"

    elif filters.get("group_by") == "Item Category":
        conditions += " GROUP BY item.item_group, item.item_code"

    elif filters.get("group_by") == "Brand":
        conditions += " GROUP BY item.brand, item.item_code"


    print(conditions)

    item_data = frappe.db.sql("""
			SELECT
				item.item_code,
				item.item_name,
				item.brand,
				item.item_group,
				item.standard_rate as mrp,
				sum(ledger.actual_qty) as actual_qty,
                ledger.name
			FROM
				`tabBin` AS ledger
			INNER JOIN `tabItem` AS item
				ON ledger.item_code = item.item_code
			WHERE
				ledger.actual_qty != 0 %s""" % (conditions), as_dict=True)

    for index, data in enumerate(item_data):
        item_data[index]['total_value'] = item_data[index]['actual_qty'] * item_data[index]['mrp']
        warehouse_list = filters.get('warehouse')
        for warehouse in warehouse_list:
            actual_qty = frappe.db.get_value('Bin', {'warehouse': warehouse, 'item_code': item_data[index]['item_code']}, 'actual_qty')
            item_data[index][warehouse] = str(actual_qty) if actual_qty else '0.0'


    return item_data
