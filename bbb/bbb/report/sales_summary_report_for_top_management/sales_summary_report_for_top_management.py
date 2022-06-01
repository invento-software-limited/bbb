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
        {"label": _("Sell Include Vat"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        # {"label": _("Profit/Loss"), "fieldname": "profit_loss", "fieldtype": "Currency", "width": 120,
        #  "convertible": "rate", "options": "currency"},
        {"label": _("Sell Exclude Vat"), "fieldname": "net_total", "fieldtype": "Currency", "width": 130,
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
        {"label": _("Card"), "fieldname": "Card", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Mobile Banking"), "fieldname": "bKash", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rounding"), "fieldname": "cash_amount", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "vat", "fieldtype": "Currency", "width": 120,
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
    invoice_type = filters.get('switch_invoice', "Sales Invoice")

    invoice_query = """select sales_invoice.pos_profile, sales_invoice.total_taxes_and_charges as vat, sales_invoice.name,
    			sum(sales_invoice_item.price_list_rate) as unit_price, sum(sales_invoice_item.rate) as selling_rate,
    			sum(sales_invoice_item.qty) as quantity,
    			sum((sales_invoice_item.qty * item.standard_rate)) as mrp_total,
    			(sales_invoice_item.qty * item.standard_rate) - (sales_invoice_item.net_rate * sales_invoice_item.qty) as discount,
    			sum((sales_invoice_item.amount - sales_invoice_item.net_amount)) as special_discount,
    			sum(sales_invoice_item.net_amount)as net_amount, sum(sales_invoice_item.amount) as total_amount, sales_invoice.customer_name,
    			sales_invoice.total, sales_invoice.grand_total, sales_invoice.net_total
    		from (`tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item)
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s group by sales_invoice.name order by sales_invoice.name""" % (invoice_type, invoice_type, conditions)


    mode_of_payment_query = """select invoice.pos_profile, invoice.vat, invoice.mrp_total, invoice.discount, invoice.special_discount, invoice.name,
                invoice.net_amount, invoice.total_amount, invoice.total, invoice.grand_total, invoice.net_total, sum(payment.amount) as payment_amount,
                payment.type as payment_type
                from (%s) as invoice left join `tabSales Invoice Payment` payment on invoice.name=payment.parent group by invoice.name""" % invoice_query


    pos_profile_query = """select pos_profile, count(name) as number_of_invoice, sum(vat) as vat, sum(mrp_total) as mrp_total,
    		 sum(discount) as discount, sum(special_discount) as special_discount, (sum(discount) + sum(special_discount)) as total_discount,
    		  format(((sum(discount) + sum(special_discount)) / sum(mrp_total)) * 100, 1) as discount_percentage, sum(net_amount) as net_amount,
    		  sum(total_amount) as total_amount, sum(total) as total, sum(grand_total) as grand_total, sum(net_total) as net_total,
    		  (sum(net_total) / count(name)) as basket_value, sum(if(payment_type='Cash', payment_amount, 0)) as Cash,
    		  sum(if(payment_type='bKash', payment_amount, 0)) as bKash, sum(if(payment_type='City Card', payment_amount, 0)) as Card
    		  from (%s) as Tab1 group by pos_profile""" % mode_of_payment_query

    query_result = frappe.db.sql(pos_profile_query, as_dict=1)
    return query_result