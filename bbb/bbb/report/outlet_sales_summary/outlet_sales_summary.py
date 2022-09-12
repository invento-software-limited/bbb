# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Text", "width": 100},
        {"label": _("Invoice Id"), "fieldname": "name", "fieldtype": "Link", "width": 180, "options": "Sales Invoice"},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "width": 200, "options": "Customer"},
        {"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Int", "width": 90},
        {"label": _("Net Total"), "fieldname": "net_total", "fieldtype": "Currency", "width": 100, "convertible": "rate","options": "currency"},
        {"label": _("Vat"), "fieldname": "total_taxes_and_charges", "fieldtype": "Currency", "width": 100, "convertible": "rate","options": "currency"},
        {"label": _("Rounded Total"), "fieldname": "rounded_total", "fieldtype": "Currency", "width": 130, "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = ["voucher.is_sales = 1"]

    if filters.get("from_date"):
        conditions.append("voucher.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("voucher.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("outlet"):
        conditions.append("voucher.pos_profile = '%s'" % filters.get("outlet"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql( """SELECT voucher.posting_date, voucher.name, voucher.customer, voucher.total_qty, voucher.net_total, voucher.total_taxes_and_charges, voucher.pos_profile, voucher.rounded_total FROM `tabPOS Invoice` voucher WHERE voucher.docstatus=1 and %s""" % conditions, as_dict=1, debug=1)

    return query_result