# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data



def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("icse.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("icse.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("source_company"):
        conditions.append("icse.source_company= '%s'" % filters.get("source_company"))

    if filters.get("source_warehouse"):
        conditions.append("icse.source_warehouse = '%s'" % filters.get("source_warehouse"))

    if filters.get("target_company"):
        conditions.append("icse.target_company= '%s'" % filters.get("target_company"))

    if filters.get("target_warehouse"):
        conditions.append("icse.target_warehouse = '%s'" % filters.get("target_warehouse"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Time"), "fieldname": "posting_time", "fieldtype": "Time", "width": 80},
        {"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "options": "Inter Company Stock Entry","width": 170},
        {"label": _("Source Company"), "fieldname": "source_company", "fieldtype": "Link", "options":"Company", "width": 146},
        {"label": _("Source Warehouse"), "fieldname": "source_warehouse", "fieldtype": "Link", "options":"Warehouse", "width": 170},
        {"label": _("Target Company"), "fieldname": "target_company", "fieldtype": "Link", "options":"Company", "width": 160},
        {"label": _("Target Warehouse"), "fieldname": "target_warehouse", "fieldtype": "Link", "options":"Warehouse", "width": 170},
        {"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 100},
        {"label": _("Total Amount"), "fieldname": "total_amount", "fieldtype": "Currency", "convertible": "rate", "options": "currency", "width": 100},
	]
    return columns

def get_data(filters):
	conditions = get_conditions(filters)

	query = """Select icse.name, icse.posting_date, icse.posting_time, icse.source_company, icse.source_warehouse, icse.target_company,
	icse.target_warehouse, icse.total_qty, icse.total_amount From `tabInter Company Stock Entry` icse 
	where icse.docstatus=1 and {}""".format(conditions)
	query_result = frappe.db.sql(query, as_dict=1)
	return query_result