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
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Data", "width": 190},
        {"label": _("Mobile No."), "fieldname": "mobile_number", "fieldtype": "Data", "width": 190},
        {"label": _("Last Invoice Date"), "fieldname": "last_invoice_date", "fieldtype": "Date", "width": 190},
    ]
    return columns

def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("invoice.posting_date >= '%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("invoice.posting_date <= '%s'" % filters.get("to_date"))

    if conditions:
        return " and ".join(conditions)

    return ''

def get_invoice_data(filters):
    conditions = get_conditions(filters)
    invoice_type = "Sales Invoice"
    has_purchased = False if filters.get("purchase_status") == "No Purchase" else True
    customer_filter = "in" if has_purchased else "not in"
    customer_group = filters.get("customer_group")
    customer_group_filter = "and customer.customer_group = '%s'" % customer_group if customer_group else ""

    if has_purchased and filters.get('only_consultancy'):
        consultancy_query = """select invoice.customer, invoice.posting_date from `tabSales Invoice Item` item join
                        `tab%s` invoice on item.parent=invoice.name where item.item_group = 'Consultancy' and %s
                        group by invoice.name""" % (invoice_type, conditions)

        except_consultancy_query = """select invoice.customer, invoice.posting_date from `tabSales Invoice Item` item join 
                        `tab%s` invoice on item.parent=invoice.name where item.item_group != 'Consultancy'
                         and %s group by invoice.name""" % (invoice_type, conditions)

        customer_query = """select tab.customer, tab.posting_date from (%s) as tab where tab.customer not in
                            (select customer from (%s) as tab2)""" % (consultancy_query, except_consultancy_query)
    else:
        customer_query = """select invoice.name as invoice, invoice.customer, invoice.posting_date 
                            from `tab%s` invoice where %s""" % (invoice_type, conditions)

    if has_purchased:
        customer_info_query = """select max(invoice.posting_date) as last_invoice_date, customer.name as customer, 
                            customer.mobile_number, customer.customer_group, customer.customer_type from (%s) as invoice
                            join `tabCustomer` customer on invoice.customer = customer.name where %s %s group by 
                            invoice.customer order by max(invoice.posting_date) desc """ % (customer_query, conditions, customer_group_filter)
    else:
        customer_info_query = """select customer.name as customer, customer.mobile_number,
                            customer.customer_group, customer.customer_type from `tabCustomer` customer where customer.name %s
                            (select invoice.customer from (%s) invoice) %s""" % (customer_filter, customer_query, customer_group_filter)

    # print(customer_info_query)
    return frappe.db.sql(customer_info_query, as_dict=1)



