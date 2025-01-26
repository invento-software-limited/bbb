# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_service_data(filters)
    # time = frappe.format('3700', {'fieldtype': 'Duration'})
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("View"), "fieldname": "view", "fieldtype": "Text", "width": 80},
        {"label": _("Service Name"), "fieldname": "service_name", "fieldtype": "Text", "width": 600},
        {"label": _("Outlet"), "fieldname": "location", "fieldtype": "Text", "width": 100},
        {"label": _("Service Person 1"), "fieldname": "service_person_1", "fieldtype": "Text", "width": 150},
        {"label": _("Service Person 2"), "fieldname": "service_person_2", "fieldtype": "Text", "width": 150},
        {"label": _("Service Person 3"), "fieldname": "service_person_3", "fieldtype": "Text", "width": 150},
        {"label": _("Service Person 3"), "fieldname": "service_person_4", "fieldtype": "Text", "width": 150},
        {"label": _("Total Service Time"), "fieldname": "total_service_time", "fieldtype": "Text", "width": 150},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Text", "width": 150},
    ]
    return columns


def get_conditions(filters):

    conditions = []
    if filters.get("from_date"):
        conditions.append("service_record.service_date >= '%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("service_record.service_date <= '%s'" % filters.get("to_date"))
    if filters.get("service_name"):
        conditions.append("service_record.service_code = '%s'" % filters.get("service_name"))
    if filters.get("location"):
        conditions.append("service_record.location = '%s'" % filters.get("location"))
    if filters.get("service_person_1"):
        conditions.append("service_record.service_person_1 = '%s'" % filters.get("service_person_1"))
    if filters.get("service_person_2"):
        conditions.append("service_record.service_person_2 = '%s'" % filters.get("service_person_2"))
    if filters.get("service_person_3"):
        conditions.append("service_record.service_person_3 = '%s'" % filters.get("service_person_3"))
    if filters.get("service_person_4"):
        conditions.append("service_record.service_person_4 = '%s'" % filters.get("service_person_4"))
    if filters.get("status"):
        conditions.append("service_record.status = '%s'" % filters.get("status"))
    if filters.get("company"):
        conditions.append("service_record.company = '%s'" % filters.get("company"))

    if conditions:
        conditions = " and ".join(conditions)

    return conditions


def get_service_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql("""
    SELECT name,
    service_name,
    invoice_no,
    location,
    service_person_1,
    service_person_2,
    service_person_3,
    service_person_4,
    total_service_time,
    status,
    company
    FROM `tabService Record` service_record
    WHERE %s""" % (conditions), as_dict=1)

    return query_result
