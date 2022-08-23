# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_invoice_data(filters)
	return columns, data


def get_columns():
	"""return columns"""
	columns = [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 400},
		# {"label": _("Customer Type"), "fieldname": "customer_type", "fieldtype": "Data", "width": 160},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "POS Profile",
		 "width": 200},
		{"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Data", "width": 200},
		{"label": _("Expiry Date"), "fieldname": "expiry_date", "fieldtype": "Date", "width": 200},
		# {"label": _("Expire Before"), "fieldname": "expire_before", "fieldtype": "Data", "width": 190},
	]
	return columns


def get_conditions(filters):
	conditions = []

	if filters.get("from_date"):
		conditions.append("item.end_of_life >= '%s'" % filters.get("from_date"))
	if filters.get("to_date"):
		conditions.append("item.end_of_life <= '%s'" % filters.get("to_date"))

	if conditions:
		conditions = " and ".join(conditions)

	return conditions


def get_invoice_data(filters):
	conditions = get_conditions(filters)
	warehouse = filters.get("warehouse", "")
	query_filters = []

	if warehouse:
		query_filters.append("stock.warehouse = '%s'" % warehouse)
	if filters.get("item"):
		query_filters.append("stock.item_code = '%s'" % filters.get("item"))

	query_filters = "where " + " and ".join(query_filters) if query_filters else ""
	conditions = "where " + conditions if conditions else ""

	stock_query = """select stock.item_code, sum(stock.actual_qty) as quantity, 
					(case when '%s'= '' then "All Warehouse" else stock.warehouse end) as warehouse
					 from `tabBin` stock %s group by stock.item_code""" % (warehouse, query_filters)

	stock_query_with_item = """select item.item_code, item.item_name, quantity, stock.warehouse, 
							item.end_of_life as expiry_date from (%s) as stock inner join `tabItem` item 
							on item.name = stock.item_code %s order by item.end_of_life""" % (stock_query, conditions)

	query_result = frappe.db.sql(stock_query_with_item, as_dict=1)
	# print(query_result)
	return query_result