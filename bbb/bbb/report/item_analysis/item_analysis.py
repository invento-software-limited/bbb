# Copyright (c) 2013, Invento Bangladesh and contributors
# For license information, please see license.txt

# import frappe

# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt
from __future__ import unicode_literals, print_function

import frappe
from frappe import _
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition


def execute(filters=None):
    columns = get_columns()

    data = get_all_product_group(filters)
    message = "Here is a message"
    chart = get_chart(data, filters)

    return columns, data, message, chart


def get_columns():
    """ Columns of Report Table"""
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "width": 100},
        {"label": _("Item Name"), "fieldname": "item_name", "width": 300},
        {"label": _("Item Group"), "fieldname": "item_group", "width": 250},
        {"label": _("Outlet"), "fieldname": "pos_profile", "width": 175},
        {"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 125},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150},
    ]


def get_all_product_group(filters):
    conditions, sort_by = get_product_conditions(filters)
    item_group = filters.get('item_group', '')

    if item_group == "Product":
        quantity_sub_query = """SUM(CASE WHEN invoice.sale_type='Advance Sale' THEN 0 ELSE item.stock_qty END) as quantity"""
    else:
        quantity_sub_query = """SUM(item.stock_qty) as quantity"""

    query_string = """SELECT item.item_code as item_code, item.item_name as item_name, %s,
        			SUM(item.net_amount) as amount, item.item_group as item_group, invoice.pos_profile as pos_profile
        			FROM `tabSales Invoice Item` item
        			LEFT JOIN  `tabSales Invoice` invoice ON (item.parent = invoice.name)
        			WHERE invoice.docstatus = 1 %s GROUP BY item.item_name %s
        		    """ % (quantity_sub_query, conditions, sort_by)

    query_result = frappe.db.sql(query_string, as_dict=1, debug=0)
    return query_result


def get_product_conditions(filters):
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')
    conditions = ""

    if from_date:
        conditions += " and invoice.posting_date >= '%s'" % from_date

    if to_date:
        conditions += " and invoice.posting_date <= '%s'" % to_date

    if filters.get("item_group"):
        conditions += (" and " + get_item_group_condition(filters.get("item_group")))

    if filters.get("pos_profile"):
        conditions += " and invoice.pos_profile = '%s'" % filters.get("pos_profile")

    if filters.get("company"):
        conditions += " and invoice.company = '%s'" % filters.get("company")

    # order_by = filters.get('order_by').lower()
    sort_by = "" if filters.get('sort_by') == "Ascending" else "DESC"

    return (conditions, sort_by)


def get_chart(data, filters):
    items_quantity = filters.get('items_quantity')
    data_ = data if items_quantity == "All" else data[:int(items_quantity)]

    data = {
        "labels": [item.get("item_name") for item in data_],
        "datasets": [
            {"name": "Quantity", "values": [item.get("quantity") for item in data_]},
            {"name": "Amount", "values": [item.get("amount")+2000 for item in data_]}
        ]
    }

    chart = {
        "data": data,
        "isNavigable": 1,
        "title": "Item Analysis Chart",
        "type": "line", # or 'bar', 'line', 'pie', 'percentage'
        "height": 400,
        "colors": ["purple", "#00c2bb", "light-blue"],
        "axisOptions": {
            "xAxisMode": "tick",
            "xIsSeries": True
        },
        "lineOptions": {
            "regionFill": 1, # default: 0
            "dotSize": 5 # default: 4
        },
        "barOptions": {
            "stacked": True,
            "spaceRatio": 1
        }
    }

    return chart
