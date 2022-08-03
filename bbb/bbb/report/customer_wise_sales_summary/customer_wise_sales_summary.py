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
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "POS Profile","width": 250},
        {"label": _("Mobile No."), "fieldname": "mobile_number", "fieldtype": "Data", "width": 190},
        # {"label": _("Customer Type"), "fieldname": "customer_type", "fieldtype": "Data", "width": 160},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Data", "width": 190},
        {"label": _("Outlet"), "fieldname": "pos_profile", "fieldtype": "Link", "options":"POS Profile", "width": 190},
        {"label": _("Total Invoice"), "fieldname": "total_invoice", "fieldtype": "Float", "width": 190},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "width": 190,
         "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("invoice.posting_date >= '%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("invoice.posting_date <= '%s'" % filters.get("to_date"))
    if filters.get('pos_profile'):
        conditions.append(("invoice.pos_profile = '%s'" % filters.get("pos_profile")))
    if filters.get('customer'):
        conditions.append(("invoice.customer = '%s'" % filters.get("customer")))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    invoice_type = filters.get('switch_invoice', "Sales Invoice")
    pos_profile = filters.get('pos_profile', '')

    invoice_query = """select count(invoice.name) as total_invoice, invoice.customer, sum(invoice.grand_total) as total_amount,
                        (case when '%s' = '' then 'All Outlet' else invoice.pos_profile end) as pos_profile
                        from `tab%s` invoice""" % (pos_profile, invoice_type)

    if conditions:
        invoice_query += """ where %s group by invoice.customer""" % conditions

    customer_sales_summary_query = """select total_invoice, total_amount, customer, customer.mobile_number, invoice_group.pos_profile,
                                    customer.customer_group, customer.customer_type from (%s) as invoice_group inner join `tabCustomer` customer 
                                    on customer.name = invoice_group.customer order by total_amount desc""" % invoice_query

    query_result = frappe.db.sql(customer_sales_summary_query, as_dict=1)
    # print(query_result)
    return query_result