# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition


def execute(filters=None):
    columns = get_columns()
    data = get_items(filters)

    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "date", "width": 100},
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Link", "options": "Purchase Invoice",
         "width": 200},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", 'options': 'Supplier', "width": 100},
        {"label": _("Total Qty"), "fieldname": "qty", "fieldtype": "text", "width": 60},
        {"label": _("Total Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        # {"label": _("Shipping Rate"), "fieldname": "shipping_rate", "fieldtype": "Currency", "width": 80,
        #  "convertible": "rate", "options": "currency"},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rounded Total"), "fieldname": "rounded_total", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("Due Amount"), "fieldname": "due_amount", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "tax", "width": 100,
         "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("invoice.posting_date>='%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("invoice.posting_date<='%s'" % filters.get("to_date"))

    if filters.get("item_group"):
        conditions.append(get_item_group_condition(filters.get("item_group")))

    if filters.get("supplier"):
        conditions.append("invoice.supplier='%s'" % filters.get("supplier"))

    if filters.get("company"):
        conditions.append("invoice.company='%s'" % filters.get("company"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    "Get items based on item code or item group or brand."
    conditions = get_conditions(filters)

    query_result = frappe.db.sql(
        """select date(invoice.posting_date) as date, invoice.name as voucher, invoice.supplier, invoice.total_qty as qty, tax.tax_amount as tax_amount,
        tax.total, invoice.company, invoice.grand_total, invoice.rounded_total, invoice.net_total as amount, sum(invoice.grand_total - invoice.outstanding_amount) as paid_amount,
         invoice.outstanding_amount as due_amount from `tabPurchase Invoice` invoice left join `tabPurchase Taxes and Charges` tax
         on invoice.name=tax.parent where invoice.docstatus = 1 and {} GROUP BY voucher, posting_date ORDER BY invoice.posting_date """.format(
            conditions), as_dict=True)

    shipping_charges = frappe.db.sql(
        """select invoice.name, tax.tax_amount, tax.total, invoice.company from `tabPurchase Invoice` invoice join `tabPurchase Invoice Item` item on
        item.parent=invoice.name join `tabPurchase Taxes and Charges` tax
         on invoice.name=tax.parent where invoice.docstatus = 1 and tax.charge_type='Actual' and {} ORDER BY invoice.posting_date""".format(
            conditions), as_dict=True)

    if shipping_charges:
        for index, result in enumerate(query_result):
            for charges in shipping_charges:
                if result.get('voucher') == charges.get('name'):
                    query_result[index].update({'shipping_rate': charges.get('tax_amount')})

    return query_result
