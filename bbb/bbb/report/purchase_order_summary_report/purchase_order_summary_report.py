# Copyright (c) 2013, Saidul Islam and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_items(filters)

    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "date", "width": 100},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier",
         "width": 150},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "text", "width": 60},
        {"label": _("Net Total"), "fieldname": "amount", "fieldtype": "Currency", "width": 150,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 200,
         "convertible": "rate", "options": "currency"},

        {"label": _("Company"), "fieldname": "company", "fieldtype": "Text", "width": 180,
         "convertible": "rate", "options": "Company"}
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("purchase_order.transaction_date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("purchase_order.transaction_date<='%s'" % filters.get("to_date"))
    if filters.get("item_brand"):
        conditions.append("purchase_order.brand='%s'" % filters.get("item_brand"))
    if filters.get("supplier"):
        conditions.append("purchase_order.supplier='%s'" % filters.get("supplier"))
    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    conditions = get_conditions(filters)
    brand = filters.get("item_brand", '')
    if brand:
        items = frappe.db.sql(
            """select date(purchase_order.transaction_date) as date, purchase_order.supplier, sum(purchase_order.total_qty) as qty, sum(purchase_order.total) as amount, purchase_order.company, 
            sum(purchase_order.total_taxes_and_charges) as tax_amount , sum(purchase_order.grand_total) as grand_total from `tabPurchase Order` purchase_order where {} group by purchase_order.transaction_date, purchase_order.supplier order by purchase_order.transaction_date ASC """.format(
                conditions),
            as_dict=True)
    else:
        items = frappe.db.sql(
            """select date(purchase_order.transaction_date) as date, purchase_order.supplier, sum(purchase_order.total_qty) as qty, sum(purchase_order.total) as amount, purchase_order.company, 
            sum(purchase_order.total_taxes_and_charges) as tax_amount , sum(purchase_order.grand_total) as grand_total from `tabPurchase Order` purchase_order where {} group by purchase_order.transaction_date, purchase_order.supplier order by purchase_order.transaction_date ASC """.format(
                conditions),
            as_dict=True)

    return items
