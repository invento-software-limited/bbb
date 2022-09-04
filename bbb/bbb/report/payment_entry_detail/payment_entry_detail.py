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
        # {"label": _("No"), "fieldname": "serial_no", "fieldtype": "Text", "width": 100},
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Text", "width": 100},
        {"label": _("Payment Type"), "fieldname": "payment_type", "fieldtype": "Text", "width": 120},
        {"label": _("Party Type"), "fieldname": "party_type", "fieldtype": "Text", "width": 100},
        {"label": _("Party"), "fieldname": "party", "fieldtype": "Text", "width": 150},
        {"label": _("Page/Serial No"), "fieldname": "page_and_serial_number", "fieldtype": "Text", "width": 100},
        {"label": _("Reference No"), "fieldname": "reference_no", "fieldtype": "Text", "width": 130},
        {"label": _("Reference Date"), "fieldname": "reference_date", "fieldtype": "Text", "width": 130},
        {"label": _("Reference Type"), "fieldname": "reference_doctype", "fieldtype": "Text", "width": 100},
        {"label": _("Reference Name"), "fieldname": "reference_name", "fieldtype": "Text", "width": 170},
        {"label": _("Grand Total"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Outstanding"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "width": 100, "options": "Cost Center"},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("payment.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("payment.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("payment_type"):
        conditions.append("payment.payment_type = '%s'" % filters.get("payment_type"))

    if filters.get("party_type"):
        conditions.append("payment.party_type = '%s'" % filters.get("party_type"))

    if filters.get("customer"):
        conditions.append("payment.party = '%s'" % filters.get("customer"))

    if filters.get("supplier"):
        conditions.append("payment.party = '%s'" % filters.get("supplier"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql(
        """SELECT payment.posting_date as date, payment.payment_type, payment.party_type, payment.party, payment.page_and_serial_number, 
        payment.reference_no, payment.reference_date, payment_account.reference_doctype, payment_account.reference_name, 
        payment_account.total_amount, payment_account.outstanding_amount, payment.cost_center
        FROM `tabPayment Entry` payment, `tabPayment Entry Reference` payment_account 
         WHERE payment.docstatus=1 and payment.name=payment_account.parent and %s""" % conditions, as_dict=1, debug=1)

    print(query_result)
    return query_result
