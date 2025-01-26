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
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Link", "options": "Sales Invoice",
         "width": 180},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", 'options': 'Customer', "width": 100},
        {"label": _("Total Qty"), "fieldname": "qty", "fieldtype": "text", "width": 100},
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
        conditions.append("sales_invoice.posting_date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("sales_invoice.posting_date<='%s'" % filters.get("to_date"))
    if filters.get("customer"):
        conditions.append("sales_invoice.customer='%s'" % filters.get("customer"))
    if filters.get("served_by"):
        conditions.append("sales_invoice.served_by='%s'" % filters.get("served_by"))
    if filters.get("company"):
        conditions.append("sales_invoice.company='%s'" % filters.get("company"))
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    conditions = get_conditions(filters)
    print(conditions)
    # items = frappe.db.sql(
    #     """select date(sales_invoice.posting_date) as date, sales_invoice.name as voucher, sales_invoice.po_no, sales_invoice.customer as customer_name, sum(item.qty) as qty, sum(item.amount) as amount,
    #     sum(tax.tax_amount) as tax_amount, sales_invoice.grand_total, sales_invoice.served_by, sales_invoice.company from `tabSales Invoice` sales_invoice
    #        left join `tabSales Invoice Item` item on item.parent=sales_invoice.name left join `tabSales Taxes and Charges` tax on sales_invoice.name=tax.parent where sales_invoice.docstatus=1 and {} group by voucher order by voucher""".format(conditions), as_dict=True)
    #

    query_result = frappe.db.sql(
        """select date(sales_invoice.posting_date) as date, sales_invoice.name as voucher, sales_invoice.customer, sales_invoice.total_qty as qty, tax.tax_amount as tax_amount, 
        tax.total, sales_invoice.company, sales_invoice.grand_total, sales_invoice.rounded_total, sales_invoice.net_total as amount, sum(sales_invoice.grand_total - sales_invoice.outstanding_amount) as paid_amount,
         sales_invoice.outstanding_amount as due_amount from `tabSales Invoice` sales_invoice left join `tabPurchase Taxes and Charges` tax 
         on sales_invoice.name=tax.parent where sales_invoice.docstatus = 1 and {} GROUP BY voucher, posting_date ORDER BY sales_invoice.posting_date """.format(
            conditions), as_dict=True)

    return query_result
