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
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer","width": 250},
        {"label": _("Mobile No."), "fieldname": "mobile_number", "fieldtype": "Data", "width": 190},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group", "width": 190},
        {"label": _("Customer Visit"), "fieldname": "total_invoice", "fieldtype": "Int", "width": 190},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 190,
         "convertible": "rate", "options": "currency"},
        {"label": _("Average Basket Value"), "fieldname": "avg_basket_value", "fieldtype": "Currency", "width": 190,
         "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = []


    if filters.get("from_date"):
        conditions.append("invoice.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("invoice.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("sales_type"):
        conditions.append("invoice.sales_type = '%s'" % filters.get("sales_type"))

    if filters.get("company"):
        conditions.append("invoice.company = '%s'" % filters.get("company"))

    if conditions:
        return " and " + " and ".join(conditions)

    return ""

def get_basket_value_conditions(filters):
    conditions = []
    min_basket_value = filters.get('min_basket_value', 0)
    max_basket_value = filters.get('max_basket_value', 0)

    if min_basket_value and max_basket_value and min_basket_value > max_basket_value:
        frappe.throw("'Max. Basket Value' can not be less than 'Min. Basket Value'")

    if min_basket_value:
        conditions.append("(total_amount/total_invoice) >= %s" % min_basket_value)
    if filters.get('max_basket_value'):
        conditions.append("(total_amount/total_invoice) <= %s" % max_basket_value)
    if filters.get("customer_group"):
        conditions.append("customer.customer_group = '%s'" % filters.get("customer_group"))

    if conditions:
        return " where " + " and ".join(conditions)

    return ""

def get_invoice_data(filters):
    conditions = get_conditions(filters)
    invoice_type = "Sales Invoice"
    basket_value_conditions = get_basket_value_conditions(filters)

    invoice_query = """select count(invoice.name) as total_invoice, invoice.customer, sum(invoice.grand_total) as total_amount
                    from `tab%s` invoice where invoice.docstatus = 1 %s group by invoice.customer""" % (invoice_type, conditions)

    customer_sales_summary_query = """select total_invoice, total_amount, customer, customer.mobile_no,
                                    (total_amount/total_invoice) as avg_basket_value, customer.customer_group,
                                    customer.customer_type from (%s) as invoice_group inner join `tabCustomer` customer
                                    on customer.name = invoice_group.customer %s order by total_amount desc""" % (invoice_query, basket_value_conditions)

    query_result = frappe.db.sql(customer_sales_summary_query, as_dict=1)
    return query_result
