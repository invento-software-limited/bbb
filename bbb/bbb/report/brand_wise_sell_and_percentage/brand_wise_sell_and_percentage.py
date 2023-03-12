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
        # {"label": _("No"), "fieldname": "serial_no", "fieldtype": "Text", "width": 100},
        {"label": _("Brand Name"), "fieldname": "brand", "fieldtype": "Text", "width": 180},
        {"label": _("MRP Amount"), "fieldname": "mrp_total", "fieldtype": "Currency", "width": 180,
         "convertible": "rate", "options": "currency"},
        {"label": _("Bill amount"), "fieldname": "bill_amount", "fieldtype": "Currency", "width": 180,
         "convertible": "rate", "options": "currency"},
        {"label": _("Unit Qty"), "fieldname": "total_item_qty", "fieldtype": "Int", "width": 180,
         "convertible": "rate", "options": "currency"},
        {"label": _("Sales %"), "fieldname": "sales_percentage", "fieldtype": "Text", "width": 150, },
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("sales_invoice.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("sales_invoice.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("outlet"):
        conditions.append("sales_invoice.pos_profile = '%s'" % filters.get("outlet"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    invoice_type = filters.get('switch_invoice')
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.grand_total, sales_invoice.served_by, sales_invoice.total_qty as unit_qty, sales_invoice.name, 
    			item.standard_rate as unit_price, sales_invoice_item.rate as selling_rate,
    			sales_invoice_item.qty as quantity, sales_invoice_item.brand,
    			(sales_invoice_item.qty * item.standard_rate) as mrp_total,
    			 sales_invoice_item.net_amount, sales_invoice_item.amount as total_amount,
    			 sales_invoice.total, sales_invoice.grand_total, sales_invoice.other_charges_calculation, sales_invoice.net_total
    		from `tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.name
    		""" % (invoice_type, invoice_type, conditions), as_dict=1)

    data = {}
    total_amount = 0
    for result in query_result:
        total_amount += result.get('total_amount')
        if data.get(result.get('brand')):
            pos_data = data.get(result.get('brand'))
            pos_data['mrp_total'] = pos_data['mrp_total'] + result['mrp_total']
            pos_data['total_item_qty'] = pos_data['total_item_qty'] + result['quantity']
            pos_data['total_amount'] = pos_data['total_amount'] + result['total_amount']

        else:
            result['total_item_qty'] = result['quantity']
            data[result.get('brand')] = result

    pos_wise_list_data = []
    for key, invoice_data in data.items():
        invoice_data['bill_amount'] = invoice_data['total_amount']
        invoice_data['sales_percentage'] = "{:.2f}".format(
            (invoice_data['total_amount'] / total_amount) * 100)
        pos_wise_list_data.append(invoice_data)
    return pos_wise_list_data

