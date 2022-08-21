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
        {"label": _("Branch Name"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile",
         "width": 100},
        {"label": _("Total Invoice"), "fieldname": "number_of_invoice", "fieldtype": "Int", "width": 110},
        {"label": _("Sell Include Vat"), "fieldname": "sell_include_vat", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Profit/Loss"), "fieldname": "profit_loss", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Sell Exclude Vat"), "fieldname": "sell_exclude_vat", "fieldtype": "Currency", "width": 130,
         "convertible": "rate", "options": "currency"},
        {"label": _("Basket Value"), "fieldname": "basket_value", "fieldtype": "Float", "width": 120},
        {"label": _("Total MRP Price"), "fieldname": "mrp_total", "fieldtype": "Currency", "width": 150,
         "convertible": "rate", "options": "currency"},
        {"label": _("Discount"), "fieldname": "discount", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Special Discount"), "fieldname": "special_discount", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Discount"), "fieldname": "total_discount", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Discount %"), "fieldname": "discount_percentage", "fieldtype": "Text", "width": 120},
        {"label": _("Cash"), "fieldname": "Cash", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("bKash"), "fieldname": "bKash", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Nagad"), "fieldname": "Nagad", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rocket"), "fieldname": "Rocket", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("City Card"), "fieldname": "City Card", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("DBBL"), "fieldname": "DBBL", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("EBL"), "fieldname": "EBL", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("UCB"), "fieldname": "UCB", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rounding"), "fieldname": "rounding_adjustment", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "total_taxes_and_charges", "fieldtype": "Currency", "width": 120,
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
    invoice_type = filters.get('switch_invoice', "POS Invoice")
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.pos_profile, sales_invoice.total_taxes_and_charges as vat, sales_invoice.name, 
    			sales_invoice_item.price_list_rate as unit_price, sales_invoice_item.rate as selling_rate,
    			sales_invoice_item.qty as quantity, sales_invoice.rounding_adjustment, 
    			(sales_invoice_item.qty * item.standard_rate) as mrp_total,
    			(sales_invoice_item.qty * item.buying_rate) as buying_total,
    			((sales_invoice_item.qty * sales_invoice_item.discount_amount)) as discount,
    			(sales_invoice.total - sales_invoice.net_total) as special_discount,
    			 sales_invoice_item.net_amount, sales_invoice_item.amount as total_amount, sales_invoice.customer_name, 
    			 sales_invoice.total, sales_invoice.rounded_total, sales_invoice.total_taxes_and_charges, sales_invoice.net_total, sales_invoice.rounding_adjustment
    		from `tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.name
    		""" % (invoice_type, invoice_type, conditions), as_dict=1)

    payment_result = frappe.db.sql("""
    		select
    			 sales_invoice.pos_profile, sales_invoice.change_amount, sales_invoice.name, payment.amount as payment_amount, payment.type as payment_type
    		from `tab%s` sales_invoice, `tabSales Invoice Payment` payment
    		where payment.parent = sales_invoice.name
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.name
    		""" % (invoice_type, conditions), as_dict=1)

    payments = {}
    payment_types = (frappe.get_meta("Mode of Payment").get_field("type").options).split('\n')
    payment_type_dict = {}
    for type in payment_types:
        payment_type_dict[type] = 0

    for payment in payment_result:
        if payment.get('pos_profile') in payments:
            pos_payment = payments.get(payment.get('pos_profile'))

            if pos_payment.get(payment.get('payment_type')):
                if payment.get('payment_type') == 'Cash':
                    pos_payment[payment.get('payment_type')] = (pos_payment[payment.get('payment_type')] + payment.get(
                        'payment_amount')) - payment.get('change_amount', 0)
                else:
                    pos_payment[payment.get('payment_type')] = pos_payment[payment.get('payment_type')] + payment.get(
                        'payment_amount')
            else:
                pos_payment[payment.get('payment_type')] = payment.get('payment_amount')
        else:
            payments[payment.get('pos_profile')] = payment_type_dict
            if payment.get('payment_type') == 'Cash':
                payments[payment.get('pos_profile')][payment.get('payment_type')] = payment.get('payment_amount') - payment.get('change_amount')
            else:
                payments[payment.get('pos_profile')][payment.get('payment_type')] = payment.get('payment_amount')

    data = {}
    for result in query_result:
        if data.get(result.get('pos_profile')):
            pos_data = data.get(result.get('pos_profile'))
            pos_data['mrp_total'] = pos_data['mrp_total'] + result['mrp_total']
            pos_data['discount'] = pos_data['discount'] + result['discount']
            pos_data['discount'] = pos_data['discount'] + result['discount']

            if result.get('name') != pos_data.get('name'):
                pos_data['number_of_invoice'] += 1
                pos_data['rounding_adjustment'] = pos_data['rounding_adjustment'] + result['rounding_adjustment']
                pos_data['net_total'] = pos_data['net_total'] + result['net_total']
                pos_data['buying_total'] = pos_data['buying_total'] + result['buying_total']
                pos_data['special_discount'] = pos_data['special_discount'] + result['special_discount']
                pos_data['total'] = pos_data['total'] + result['total']
                pos_data['total_taxes_and_charges'] = pos_data['total_taxes_and_charges'] + result[
                    'total_taxes_and_charges']
                pos_data['rounded_total'] = pos_data['rounded_total'] + result['rounded_total']
                pos_data['name'] = result.get('name')
                pos_data['vat'] = pos_data['vat'] + result['vat']
                pos_data['rounding_adjustment'] = pos_data['rounding_adjustment'] + result['rounding_adjustment']
        else:
            result['number_of_invoice'] = 1
            result['total_item_qty'] = result['quantity']
            data[result.get('pos_profile')] = result

    pos_wise_list_data = []
    for key, invoice_data in data.items():
        payment_data = payments.get(key, {})
        invoice_data.update(payment_data)
        total_discount = float(invoice_data['discount']) + float(invoice_data['special_discount'])
        invoice_data['basket_value'] = (
                float(invoice_data['rounded_total']) / float(invoice_data['number_of_invoice']))
        invoice_data['total_discount'] = total_discount
        invoice_data['sell_include_vat'] = invoice_data['rounded_total']
        invoice_data['sell_exclude_vat'] = invoice_data['net_total']
        invoice_data['profit_loss'] = invoice_data['net_total'] - invoice_data['buying_total']
        invoice_data['discount_percentage'] = str(
            float("{:.2f}".format((total_discount / invoice_data['mrp_total']) * 100)))
        pos_wise_list_data.append(invoice_data)
    return pos_wise_list_data
