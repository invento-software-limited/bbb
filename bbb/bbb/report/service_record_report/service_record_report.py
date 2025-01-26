# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_service_data(filters)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("View"), "fieldname": "view", "fieldtype": "Text", "width": 80},
        {"label": _("Service Name"), "fieldname": "service_name", "fieldtype": "Text", "width": 600},
        {"label": _("Service Person 1"), "fieldname": "service_person_1", "fieldtype": "Text", "width": 150},
        {"label": _("Service Person 2"), "fieldname": "service_person_2", "fieldtype": "Text", "width": 150},
        {"label": _("Service Person 3"), "fieldname": "service_person_3", "fieldtype": "Text", "width": 150},
        {"label": _("Service Person 3"), "fieldname": "service_person_4", "fieldtype": "Text", "width": 150},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Text", "width": 150},
    ]
    return columns


def get_conditions(filters):

    conditions = []
    if filters.get("from_date"):
        conditions.append("service_record.service_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("service_record.service_date <= '%s'" % filters.get("to_date"))

    if filters.get("status"):
        conditions.append("service_record.status = '%s'" % filters.get("status"))

    if conditions:
        conditions = " and ".join(conditions)

    return conditions


def get_service_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql("""
    SELECT name,
    service_name,
    service_person_1,
    service_person_2,
    service_person_3,
    service_person_4,
    status
    FROM `tabService Record` service_record
    WHERE %s""" % (conditions), as_dict=1)

    return query_result
