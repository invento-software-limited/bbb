# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition


def execute(filters=None):
    columns = get_columns()
    data = get_items(filters)

    return columns, data

#npZ7to3292m9m5UVWWZ4fTifa_7f8wKnLyJXwrmb7fo=
def get_columns():
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "date", "width": 100},
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Link", "options": "Sales Order", "width": 130},
        {"label": _("Customer Purchase Order"), "fieldname": "po_no", "fieldtype": "text", "width": 90},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "text", "width": 150},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "text", "width": 60},
        {"label": _("Total Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 150,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("Served By"), "fieldname": "served_by", "fieldtype": "Link", "width": 180,
         "convertible": "rate", "options": "Served By"},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "Text", "width": 120,
         "convertible": "rate", "options": "Company"}
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("sales_order.transaction_date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("sales_order.transaction_date<='%s'" % filters.get("to_date"))
    if filters.get("customer"):
        conditions.append("sales_order.customer='%s'" % filters.get("customer"))
    if filters.get("served_by"):
        conditions.append("sales_order.served_by='%s'" % filters.get("served_by"))
    if filters.get("company"):
        conditions.append("sales_order.company='%s'" % filters.get("company"))
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    conditions = get_conditions(filters)
    print(conditions)
    items = frappe.db.sql(
        """select date(sales_order.transaction_date) as date, sales_order.name as voucher, sales_order.po_no, sales_order.customer as customer_name, sum(item.qty) as qty, sum(item.amount) as amount, 
        sum(tax.tax_amount) as tax_amount, sales_order.grand_total, sales_order.served_by, sales_order.company from `tabSales Order` sales_order
           left join `tabSales Order Item` item on item.parent=sales_order.name left join `tabSales Taxes and Charges` tax on sales_order.name=tax.parent where sales_order.docstatus=1 and {} group by voucher order by voucher""".format(conditions), as_dict=True)
    return items
