# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate
import datetime


def execute(filters=None):
    columns, data = get_columns(), get_data(filters)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Link", "options": "Customer",
         "width": 250},
        {"label": _("Customer Group"), "fieldname": "customer_group", "fieldtype": "Link", "options": "Customer Group",
         "width": 190},
        {"label": _("Source"), "fieldname": "source", "fieldtype": "link", "options": "Lead Source", "width": 190},
        {"label": _("Day"), "fieldname": "day", "fieldtype": "Text", "width": 190},
        {"label": _("Mobile No."), "fieldname": "mobile_number", "fieldtype": "Data", "width": 190},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("customer_group"):
        conditions.append("customer.customer_group = '%s'" % filters.get("customer_group"))

    if filters.get("customer"):
        conditions.append("customer.name = '%s'" % filters.get("customer"))

    if filters.get("company"):
        conditions.append("customer.company = '%s'" % filters.get("company"))

    conditions.append("customer.disabled = 0")

    today = getdate(nowdate())
    next_day = today
    type = filters.get('type')
    if type == "Next 7 Days":
        next_day = getdate(add_days(today, 6))
    elif type == "Next 30 Days":
        next_day = getdate(add_days(today, 29))


    conditions.append("customer.birth_month = {}".format(today.month))
    conditions.append("customer.birth_month = {}".format(next_day.month))
    if conditions:
        return " and ".join(conditions)

    return ""


def get_data(filters):
    conditions = get_conditions(filters)
    customer_query = """select customer_name, mobile_number, customer_group, source, birth_day, birth_month, birth_year
    from `tabCustomer` customer where birth_day > 0 and birth_month > 0 and (%s)""" % conditions

    query_result = frappe.db.sql(customer_query, as_dict=1)

    customer_birthday_list = []
    for result in query_result:
        today = getdate(nowdate())
        type = filters.get('type')
        if type == "Next 7 Days":
            next_date = getdate(add_days(getdate(add_days(today, 1)), 7))
        elif type == "Next 30 Days":
            next_date = getdate(add_days(getdate(add_days(today, 1)), 30))
        else:
            next_date = getdate(nowdate())

        new_day = result.get('birth_day', 0)
        new_month = result.get('birth_month', 0)
        if new_day > 0 and new_month > 0 and new_month == today.month:
            customer_birth_date = getdate(str(today.year) + '-' + str(new_month) + '-' + str(new_day))
        elif new_day > 0 and new_month > 0 and new_month == next_date.month:
            customer_birth_date = getdate(str(next_date.year) + '-' + str(new_month) + '-' + str(new_day))
        else:
            continue

        if customer_birth_date <= next_date:
            if result['birth_day'] == 1:
                result['day'] = (
                    getdate('1900-' + str(result['birth_month']) + '-' + str(result['birth_day']))).strftime("%-dst %B")
            elif result['birth_day'] == 2:
                result['day'] = (
                    getdate('1900-' + str(result['birth_month']) + '-' + str(result['birth_day']))).strftime("%-dnd %B")
            elif result['birth_day'] == 3:
                result['day'] = (
                    getdate('1900-' + str(result['birth_month']) + '-' + str(result['birth_day']))).strftime("%-drd %B")
            else:
                result['day'] = (
                    getdate('1900-' + str(result['birth_month']) + '-' + str(result['birth_day']))).strftime("%-dth %B")
            customer_birthday_list.append(result)
    return customer_birthday_list
