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
        {"label": _("Branch Name"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile",
         "width": 120},
        {"label": _("Total Invoice"), "fieldname": "number_of_invoice", "fieldtype": "Int", "width": 120},
        {"label": _("Sell Include Vat"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 145,
         "convertible": "rate", "options": "currency"},
        {"label": _("Sell Exclude Vat"), "fieldname": "net_total", "fieldtype": "Currency", "width": 145,
         "convertible": "rate", "options": "currency"},
        {"label": _("Additional Discount"), "fieldname": "additional_discount", "fieldtype": "Currency", "width": 140,
         "convertible": "rate", "options": "currency"},
        {"label": _("Cash"), "fieldname": "Cash", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Card"), "fieldname": "Card", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Mobile Banking"), "fieldname": "bKash", "fieldtype": "Currency", "width": 140,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "vat", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Cost"), "fieldname": "total_buying_rate", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Card %"), "fieldname": "card_payment_percentage", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rounding"), "fieldname": "rounding", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Profit/Loss"), "fieldname": "profit_loss", "fieldtype": "Currency", "width": 120,
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
            sales_invoice.discount_amount as additional_discount, sales_invoice.total, sales_invoice.rounding_adjustment,
            sales_invoice.grand_total, sales_invoice.net_total, sum(if(payment.type='Cash', payment.amount, 0)) as Cash,
    		sum(if(payment.type='bKash', payment.amount, 0)) as bKash, sum(if(payment.type='City Card', payment.amount, 0)) as Card
    		from `tab%s` sales_invoice, `tabSales Invoice Payment` payment where sales_invoice.name=payment.parent and
    		sales_invoice.docstatus = 1 and %s group by sales_invoice.name order by sales_invoice.name""" % (invoice_type, conditions)


    pos_profile_query = """select pos_profile, count(name) as number_of_invoice, sum(vat) as vat,
                        sum(additional_discount) as additional_discount, sum(grand_total) as grand_total,
                        sum(net_total) as net_total, sum(Cash) as Cash, sum(bKash) as bKash, sum(Card) as Card,
                        sum(rounding_adjustment) as rounding from (%s) as Tab1 group by pos_profile""" % invoice_query

    query_result = frappe.db.sql(pos_profile_query, as_dict=1)
    return query_result
