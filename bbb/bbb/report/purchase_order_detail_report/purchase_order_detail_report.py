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
        {"label": _("Voucher"), "fieldname": "voucher", "fieldtype": "Link", "options": "Purchase Order", "width": 100},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 100},
        {"label": _("Order Confirmation No"), "fieldname": "order_confirmation_no", "fieldtype": "text", "width": 100},
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "text", "options": "Item", "width": 90},
        {"label": _("Item Name"), "fieldname": "item_name", "width": 180},
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
        # {"label": _("Shipping Rate"), "fieldname": "shipping_rate", "fieldtype": "Currency", "width": 90,
        #  "convertible": "rate", "options": "currency"},
        {"label": _("Company"), "fieldname": "company", "fieldtype": "text", "width": 90}
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("purchase_order.transaction_date>='%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("purchase_order.transaction_date<='%s'" % filters.get("to_date"))

    if filters.get("item_code"):
        conditions.append("item.item_code='%s'" % filters.get("item_code"))

    if filters.get("item_group"):
        conditions.append(get_item_group_condition(filters.get("item_group")))

    if filters.get("item_brand"):
        conditions.append("item.brand='%s'" % filters.get("item_brand"))
    if filters.get("supplier"):
        conditions.append("purchase_order.supplier='%s'" % filters.get("supplier"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_items(filters):
    "Get items based on item code or item group or brand."
    conditions = get_conditions(filters)

    query_result = frappe.db.sql(
        """select distinct date(purchase_order.transaction_date) as date, purchase_order.name as voucher, purchase_order.supplier, purchase_order.order_confirmation_no, item.item_code, item.item_name,
        item.item_group, sum(item.qty) as qty, item.rate, item.uom, sum(item.amount) as amount, sum(tax.tax_amount) as tax_amount, sum(tax.total) as total, purchase_order.company, purchase_order.grand_total 
        from `tabPurchase Order` purchase_order 
        left join `tabPurchase Order Item` item on item.parent=purchase_order.name left join `tabPurchase Taxes and Charges` tax 
         on purchase_order.name=tax.parent where purchase_order.docstatus = 1 and {} GROUP BY item_code, voucher, transaction_date ORDER BY purchase_order.transaction_date """.format(
            conditions), as_dict=True)

    shipping_charges = frappe.db.sql(
        """select purchase_order.name, tax.tax_amount, tax.total, purchase_order.company from `tabPurchase Order` purchase_order join `tabPurchase Order Item` item on
        item.parent=purchase_order.name join `tabPurchase Taxes and Charges` tax
         on purchase_order.name=tax.parent where purchase_order.docstatus = 1 and tax.charge_type='Actual' and {} ORDER BY purchase_order.transaction_date""".format(
            conditions), as_dict=True)

    if shipping_charges:
        for index, result in enumerate(query_result):
            for charges in shipping_charges:
                if result.get('voucher') == charges.get('name'):
                    query_result[index].update({'shipping_rate': charges.get('tax_amount')})

    return query_result
