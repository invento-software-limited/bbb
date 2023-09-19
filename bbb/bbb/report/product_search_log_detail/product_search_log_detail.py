# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition


def execute(filters=None):
    print(filters)
    columns = get_columns(filters)
    data = get_items(filters)
    return columns, data


def get_columns(filters):
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "date", "width": 100},
        {"label": _("Time"), "fieldname": "p_time", "fieldtype": "time", "width": 80},
        # {"label": _("Item Code"), "fieldname": "product", "fieldtype": "Link", "options": "Item", "width": 150},
        {"label": _("Item Name"), "fieldname": "product_name", "fieldtype": "Link", "options": "Item", "width": 400},
        {"label": _("Location"), "fieldname": "location", "fieldtype": "Link", 'options': 'POS Profile', "width": 100},
        {"label": _("Served By"), "fieldname": "served_by", "fieldtype": "Link", 'options': 'Served By', "width": 140},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        # {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        # {"label": _("Email"), "fieldname": "email", "fieldtype": "Data", "width": 150},
        # {"label": _("Mobile Number"), "fieldname": "mobile_number", "fieldtype": "Data", "width": 150},
    ]

    if filters.get('is_sale') == "All":
        columns.append({"label": _("Is Sold"), "fieldname": "is_sale", "width": 100})

    columns.append({"label": _("Company"), "fieldname": "company", "width": 200})

    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("product_search_log.date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("product_search_log.date<='%s'" % filters.get("to_date"))
    if filters.get("product"):
        conditions.append("product_search_log.product='%s'" % filters.get("product"))
    if filters.get("served_by"):
        conditions.append("product_search_log.served_by='%s'" % filters.get("served_by"))
    if filters.get("location"):
        conditions.append("product_search_log.location='%s'" % filters.get("location"))
    if filters.get("customer"):
        conditions.append("product_search_log.customer='%s'" % filters.get("customer"))
    if filters.get("company"):
        conditions.append("product_search_log.company='%s'" % filters.get("company"))
    if filters.get("is_sale") == "Sold Item":
        conditions.append("product_search_log.is_sale=1")
    if filters.get("is_sale") == "Unsold Item":
        conditions.append("product_search_log.is_sale=0")
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    conditions = get_conditions(filters)

    query_result = frappe.db.sql(
        """select product_search_log.date, TIME_FORMAT(product_search_log.time, "%h:%i %p") as p_time, product_search_log.product_name, (case product_search_log.is_sale when 1 then "Yes" else null end) as is_sale,
            product_search_log.served_by, product_search_log.location, product_search_log.company,
            product_search_log.product, product_search_log.customer, product_search_log.customer_name, product_search_log.location
        from `tabProduct Search Log` product_search_log where {}""".format(conditions), as_dict=True)

    return query_result
