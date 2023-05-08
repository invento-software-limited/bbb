# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate


def execute(filters=None):
    columns, data = get_columns(), get_invoice_data(filters)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Link", "options": "Customer",
         "width": 250},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group",
         "width": 190},
        {"label": _("Source"), "fieldname": "total_invoice", "fieldtype": "Int", "width": 190},
        {"label": _("Mobile No."), "fieldname": "mobile_number", "fieldtype": "Data", "width": 190},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("customer_group"):
        conditions.append("customer.customer_group = '%s'" % filters.get("customer_group"))

    if filters.get("company"):
        conditions.append("customer.company = '%s'" % filters.get("company"))

    conditions.append("customer.disabled = 0")
    if conditions:
        return " and ".join(conditions)

    return ""


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    today = getdate(nowdate())
    next_day = today
    type = filters.get('type')
    if type == "Next 7 Days":
        next_day = getdate(add_days(today, 6))
    elif type == "Next 30 Days":
        next_day = getdate(add_days(today, 29))


    # customer_query = """select customer_name, mobile_number, customer_group, source, CONCAT(birth_day,'-',birth_month,'-', birth_year) as birthday
    # from `tabCustomer` customer where birth_year != 0 and birth_month != 0 and birth_day != 0 and %s""" % conditions
    customer_query = """select customer_name, mobile_number, customer_group, source, CONCAT(birth_day,'-',birth_month,'-', birth_year) as birthday
    from `tabCustomer` customer limit 10"""
    query_result = frappe.db.sql(customer_query, as_dict=1)

    # customer_birthday_data = []
    # for customer in query_result:
    #     customer_birthday = getdate(customer.get('birthday'))
    #     if customer_birthday <= next_day:
    #         customer_birthday_data.append(customer)

    return query_result
