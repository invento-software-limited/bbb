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
        {"label": _("Voucher Type"), "fieldname": "voucher_type", "fieldtype": "Text", "width": 150},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "width": 100, "options": "Cost Center"},
        {"label": _("Account"), "fieldname": "account", "fieldtype": "Link", "width": 200, "options": "Account"},
        {"label": _("Party Type"), "fieldname": "party_type", "fieldtype": "Text", "width": 100},
        {"label": _("Party"), "fieldname": "party", "fieldtype": "Text", "width": 190},
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "width": 100, "convertible": "rate",
         "options": "currency"},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "width": 120, "convertible": "rate",
         "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("voucher.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("voucher.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("voucher_type"):
        conditions.append("voucher.voucher_type = '%s'" % filters.get("voucher_type"))

    if filters.get("company"):
        conditions.append("voucher.company = '%s'" % filters.get("company"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql(
        """SELECT voucher.posting_date as date, voucher.voucher_type, voucher_account.account, voucher_account.party_type, voucher_account.party, voucher_account.cost_center,
         voucher_account.debit, voucher_account.credit FROM `tabJournal Entry` voucher, `tabJournal Entry Account` voucher_account WHERE voucher.docstatus=1 and voucher.name=voucher_account.parent and %s""" % conditions,
        as_dict=1, debug=1)

    print(query_result)
    return query_result
