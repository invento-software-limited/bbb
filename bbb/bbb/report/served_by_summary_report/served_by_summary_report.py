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
        {"label": _("Served By Name"), "fieldname": "served_by", "fieldtype": "Link", "options": "Served By",
         "width": 180},
        {"label": _("ID"), "fieldname": "id", "fieldtype": "Text", "width": 100},
        {"label": _("Number Of Invoice"), "fieldname": "number_of_invoice", "fieldtype": "Int", "width": 100},
        {"label": _("Basket Value"), "fieldname": "basket_value", "fieldtype": "Float", "width": 120},
        {"label": _("Total MRP Price"), "fieldname": "mrp_total", "fieldtype": "Currency", "width": 180,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Sell Final"), "fieldname": "total_sell_final", "fieldtype": "Currency", "width": 180,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Sell Disc"), "fieldname": "total_discount", "fieldtype": "Currency", "width": 180,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Disc %"), "fieldname": "discount_percentage", "fieldtype": "Text", "width": 150, },
        {"label": _("Ranking"), "fieldname": "ranking", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("sales_invoice.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("sales_invoice.posting_date <= '%s'" % filters.get("to_date"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.grand_total, sales_invoice.served_by, sales_invoice.total_taxes_and_charges as vat, sales_invoice.name, 
    			sales_invoice_item.price_list_rate as unit_price, sales_invoice_item.rate as selling_rate,
    			sales_invoice_item.qty as quantity,
    			(sales_invoice_item.qty * item.standard_rate) as mrp_total,
    			((sales_invoice_item.qty * item.standard_rate) - (sales_invoice_item.rate * sales_invoice_item.qty)) as discount,
    			sales_invoice.discount_amount as special_discount,
    			 sales_invoice_item.net_amount, sales_invoice_item.amount as total_amount, sales_invoice.customer_name, 
    			 sales_invoice.total, sales_invoice.grand_total, sales_invoice.total_taxes_and_charges, sales_invoice.net_total
    		from `tabSales Invoice` sales_invoice, `tabSales Invoice Item` sales_invoice_item, `tabItem` item
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.name
    		""" % (conditions), as_dict=1)

    data = {}
    for result in query_result:
        if data.get(result.get('served_by')):
            pos_data = data.get(result.get('served_by'))
            pos_data['mrp_total'] = pos_data['mrp_total'] + result['mrp_total']
            pos_data['discount'] = pos_data['discount'] + result['discount']
            pos_data['total_item_qty'] = pos_data['total_item_qty'] + result['quantity']

            if result.get('name') != pos_data.get('name'):
                pos_data['number_of_invoice'] += 1
                pos_data['net_total'] = pos_data['net_total'] + result['net_total']
                pos_data['special_discount'] = pos_data['special_discount'] + result['special_discount']
                pos_data['total'] = pos_data['total'] + result['total']
                pos_data['total_taxes_and_charges'] = pos_data['total_taxes_and_charges'] + result[
                    'total_taxes_and_charges']
                pos_data['grand_total'] = pos_data['grand_total'] + result['grand_total']
                pos_data['name'] = result.get('name')

        else:
            result['number_of_invoice'] = 1
            result['total_item_qty'] = result['quantity']
            data[result.get('served_by')] = result

    pos_wise_list_data = []
    for key, invoice_data in data.items():
        total_discount = float(invoice_data['discount']) + float(invoice_data['special_discount'])
        invoice_data['basket_value'] = (
                float(invoice_data['grand_total']) / float(invoice_data['number_of_invoice']))
        invoice_data['total_discount'] = total_discount
        invoice_data['total_sell_final'] = invoice_data['net_total']
        invoice_data['discount_percentage'] = str(
            float("{:.2f}".format((total_discount / invoice_data['total']) * 100)))
        pos_wise_list_data.append(invoice_data)
    return pos_wise_list_data
