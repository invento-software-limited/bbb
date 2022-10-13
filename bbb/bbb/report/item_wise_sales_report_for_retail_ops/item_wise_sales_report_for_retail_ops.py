# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(filters), get_invoice_data(filters)
    return columns, data


def get_columns(filters):
    """return columns"""
    columns = []
    invoice_type = filters.get('switch_invoice', "POS Invoice")
    columns.append({"label": _("Date"), "fieldname": "posting_date", "fieldtype": "date", "width": 100})

    if invoice_type == 'POS Invoice':
        columns.append(
            {"label": _("Invoice"), "fieldname": "invoice_name", "fieldtype": "Link", "options": "POS Invoice",
             "width": 170}),
    else:
        columns.append(
            {"label": _("Invoice"), "fieldname": "invoice_name", "fieldtype": "Link", "options": "Sales Invoice",
             "width": 100}),

    columns = columns + [
        {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand",
         "width": 130},
        {"label": _("Item Category"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",
         "width": 130},
        {"label": _("Product Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item",
         "width": 150},
        {"label": _("Product Name"), "fieldname": "item_name", "fieldtype": "Link", "options": "Item",
         "width": 900},
        {"label": _("Sell Qty"), "fieldname": "sales_qty", "fieldtype": "Int", "width": 80},
        {"label": _("Current Stock"), "fieldname": "current_stock", "fieldtype": "Int", "width": 130},
        {"label": _("MRP Rate"), "fieldname": "mrp_rate", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
        {"label": _("MRP Value"), "fieldname": "mrp_value", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Sell Value"), "fieldname": "sell_value", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
    ]

    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("sales_invoice.posting_date >= '%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("sales_invoice.posting_date <= '%s'" % filters.get("to_date"))
    if filters.get("store"):
        conditions.append("sales_invoice.pos_profile = '%s'" % filters.get("store"))
    if filters.get("product_code"):
        conditions.append("sales_invoice_item.item_code = '%s'" % filters.get("product_code"))
    if filters.get("brand"):
        conditions.append("sales_invoice_item.brand = '%s'" % filters.get("brand"))
    if filters.get("item_group"):
        conditions.append("sales_invoice_item.item_group = '%s'" % filters.get("item_group"))
    if filters.get("served_by"):
        conditions.append("sales_invoice.served_by = '%s'" % filters.get("served_by"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    invoice_type = filters.get('switch_invoice', "POS Invoice")
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.pos_profile, sales_invoice.posting_date, sales_invoice.name as invoice_name, sales_invoice_item.price_list_rate as unit_price, item.item_code, 
    			sales_invoice_item.qty as sales_qty, item.standard_rate as mrp_rate, (sales_invoice_item.qty * item.standard_rate) as mrp_value,
    			(sales_invoice_item.qty * item.buying_rate) as buying_total, sales_invoice_item.net_amount, sales_invoice_item.amount as sell_value, 
    			item.brand, item.item_group, item.item_name, bin.actual_qty as current_stock
    		from `tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item, `tabBin` bin
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code and bin.item_code = item.item_code and bin.warehouse=sales_invoice.set_warehouse
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.name
    		""" % (invoice_type, invoice_type, conditions), as_dict=1)
    return query_result

#
# def get_stock_ledger_entries(filters, items):
# 	item_conditions_sql = ""
# 	if items:
# 		item_conditions_sql = "and sle.item_code in ({})".format(
# 			", ".join(frappe.db.escape(i) for i in items)
# 		)
#
# 	sl_entries = frappe.db.sql(
# 		"""
# 		SELECT
# 			concat_ws(" ", posting_date, posting_time) AS date,
# 			item_code,
# 			warehouse,
# 			actual_qty,
# 			qty_after_transaction,
# 			incoming_rate,
# 			valuation_rate,
# 			stock_value,
# 			voucher_type,
# 			voucher_no,
# 			batch_no,
# 			serial_no,
# 			company,
# 			project,
# 			stock_value_difference
# 		FROM
# 			`tabStock Ledger Entry` sle
# 		WHERE
# 			company = %(company)s
# 				AND is_cancelled = 0 AND posting_date BETWEEN %(from_date)s AND %(to_date)s
# 				{sle_conditions}
# 				{item_conditions_sql}
# 		ORDER BY
# 			posting_date asc, posting_time asc, creation asc
# 		""".format(
# 			sle_conditions=get_sle_conditions(filters), item_conditions_sql=item_conditions_sql
# 		),
# 		filters,
# 		as_dict=1,
# 	)
#
# 	return sl_entries

