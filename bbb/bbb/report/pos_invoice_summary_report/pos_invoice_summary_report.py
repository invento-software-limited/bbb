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
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Link", "options": "POS Invoice",
         "width": 180},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", 'options': 'Customer', "width": 100},
        {"label": _("Total Qty"), "fieldname": "qty", "fieldtype": "text", "width": 100},
        {"label": _("Total Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "total_taxes_and_charges", "fieldtype": "Currency", "width": 100,
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
        conditions.append("pos_invoice.posting_date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("pos_invoice.posting_date<='%s'" % filters.get("to_date"))
    if filters.get("customer"):
        conditions.append("pos_invoice.customer='%s'" % filters.get("customer"))
    if filters.get("served_by"):
        conditions.append("pos_invoice.served_by='%s'" % filters.get("served_by"))
    if filters.get("company"):
        conditions.append("pos_invoice.company='%s'" % filters.get("company"))
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    conditions = get_conditions(filters)
    # items = frappe.db.sql(
    #     """select date(pos_invoice.posting_date) as date, pos_invoice.name as voucher, pos_invoice.po_no, pos_invoice.customer as customer_name, sum(item.qty) as qty, sum(item.amount) as amount,
    #     sum(tax.tax_amount) as tax_amount, pos_invoice.grand_total, pos_invoice.served_by, pos_invoice.company from `tabPOS Invoice` pos_invoice
    #        left join `tabPOS Invoice Item` item on item.parent=pos_invoice.name left join `tabSales Taxes and Charges` tax on pos_invoice.name=tax.parent where pos_invoice.docstatus=1 and {} group by voucher order by voucher""".format(conditions), as_dict=True)
    #

    query_result = frappe.db.sql(
        """select date(pos_invoice.posting_date) as date, pos_invoice.name as voucher, pos_invoice.customer, pos_invoice.total_taxes_and_charges,pos_invoice.total_qty as qty, tax.tax_amount as tax_amount, 
        tax.total, pos_invoice.company, pos_invoice.grand_total, pos_invoice.rounded_total, pos_invoice.net_total as amount, sum(pos_invoice.grand_total - pos_invoice.outstanding_amount) as paid_amount,
         pos_invoice.outstanding_amount as due_amount from `tabPOS Invoice` pos_invoice left join `tabPurchase Taxes and Charges` tax 
         on pos_invoice.name=tax.parent where pos_invoice.docstatus = 1 and {} GROUP BY voucher, posting_date ORDER BY pos_invoice.posting_date """.format(
            conditions), as_dict=True)

    return query_result
