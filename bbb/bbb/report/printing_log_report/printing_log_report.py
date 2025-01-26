# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition


def execute(filters=None):
    columns = get_columns()
    data = get_items(filters)
    print(data)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "date", "width": 140},
        {"label": _("Invoice Number"), "fieldname": "invoice_number", "fieldtype": "Link", "options": "POS Invoice",
         "width": 250},
        {"label": _("Location"), "fieldname": "location", "fieldtype": "Link", 'options': 'POS Profile', "width": 140},
        {"label": _("Served By"), "fieldname": "served_by", "fieldtype": "Link", 'options': 'Served By', "width": 140},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options":"Customer", "width": 170},
        # {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 150},
        # {"label": _("Email"), "fieldname": "email", "fieldtype": "Data", "width": 150},
        # {"label": _("Mobile Number"), "fieldname": "mobile_number", "fieldtype": "Data", "width": 150},
        {"label": _("Total Print Count"), "fieldname": "total_print_count", "width": 140},
        {"label": _("Company"), "fieldname": "company", "width": 230},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("printing_log.date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("printing_log.date<='%s'" % filters.get("to_date"))
    if filters.get("served_by"):
        conditions.append("printing_log.served_by='%s'" % filters.get("served_by"))
    if filters.get("location"):
        conditions.append("printing_log.location='%s'" % filters.get("location"))
    if filters.get("customer"):
        conditions.append("printing_log.customer='%s'" % filters.get("customer"))
    if filters.get("company"):
        conditions.append("printing_log.company='%s'" % filters.get("company"))
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    conditions = get_conditions(filters)

    query_result = frappe.db.sql(
        """select COUNT(ALL printing_log.invoice_number) as total_print_count, printing_log.date,
            printing_log.served_by, printing_log.location, printing_log.company,
            printing_log.invoice_number, printing_log.customer, printing_log.customer_name, printing_log.location
        from `tabPrinting Log` printing_log where {} group by printing_log.invoice_number""".format(conditions), as_dict=True)

    return query_result