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
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Link", "options": "Sales Order", "width": 100},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "text", "width": 100},
        {"label": _("SO No"), "fieldname": "po_no", "fieldtype": "text", "width": 100},
        {"label": _("SO Date"), "fieldname": "po_date", "fieldtype": "text", "width": 100},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "text", "options": "Item", "width": 90},
        {"label": _("Item Name"), "fieldname": "item_name", "width": 180},
        {"label": _("Item Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 120},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",
         "width": 120},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "text", "width": 50},
        {"label": _("UOM"), "fieldname": "uom", "fieldtype": "text", "width": 60},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "tax_amount", "fieldtype": "Currency", "width": 80,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total With VAT"), "fieldname": "total", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
        {"label": _("Served By"), "fieldname": "served_by", "fieldtype": "Link", "width": 90,
         "options": "Served By"},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "text", "width": 90}
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("sales_order.transaction_date>='%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("sales_order.transaction_date<='%s'" % filters.get("to_date"))

    if filters.get("item_code"):
        conditions.append("item.item_code=%s" % filters.get("item_code"))

    if filters.get("item_group"):
        conditions.append(get_item_group_condition(filters.get("item_group")))

    if filters.get("item_brand"):
        conditions.append("item.brand='%s'" % filters.get("item_brand"))
    if filters.get("customer"):
        conditions.append("sales_order.party_name='%s'" % filters.get("customer"))
    if filters.get("company"):
        conditions.append("sales_order.company='%s'" % filters.get("company"))
    if filters.get("served_by"):
        conditions.append("sales_order.served_by='%s'" % filters.get("served_by"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    "Get items based on item code or item group or brand."
    conditions = get_conditions(filters)
    query_result = frappe.db.sql(
        """select distinct date(sales_order.transaction_date) as date, sales_order.name as voucher, sales_order.po_no, sales_order.po_date, sales_order.customer_name,
        item.item_code, item.item_name, item.brand, item.item_group, item.qty, item.rate, item.uom, item.amount, tax.tax_amount, tax.total,
        sales_order.served_by, sales_order.company from `tabSales Order Item` item left join `tabSales Order` sales_order on item.parent=sales_order.name
        left join `tabSales Taxes and Charges` tax on sales_order.name=tax.parent where sales_order.docstatus = 1 and {} ORDER BY sales_order.transaction_date""".format(
            conditions),
        as_dict=True)
    return query_result
