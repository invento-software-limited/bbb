# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt
import datetime

import frappe
from frappe import _


def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters, columns)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Pos Profile"),
            "fieldname": "pos_profile",
            "fieldtype": "Link",
            "options": "POS Profile",
            "width": 120,
        },
        {
            "label": _("Opening Id"),
            "fieldname": "opening_id",
            "fieldtype": "Link",
            "options": "POS Opening Entry",
            "width": 150,
        },
        {
            "label": _("Opening Date"),
            "fieldname": "opening_date",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Status"),
            "fieldname": "status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Closing Id"),
            "fieldname": "closing_id",
            "fieldtype": "Link",
            "options": "POS Closing Entry",
            "width": 150,
        },
        {
            "label": _("Closing Date"),
            "fieldname": "closing_date",
            "fieldtype": "Data",
            "width": 120,
        },
    ]


def get_data(filters, columns):
    item_price_qty_data = []
    item_price_qty_data = get_item_price_qty_data(filters)
    return item_price_qty_data


def get_item_price_qty_data(filters):
    condition_list = []
    conditions = None
    if filters.get("from_date"):
        condition_list.append("pos_opening_entry.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        condition_list.append("pos_opening_entry.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("pos_profile"):
        condition_list.append("pos_opening_entry.pos_profile = '%s'" % filters.get("pos_profile"))

    if filters.get("status"):
        condition_list.append("pos_opening_entry.status = '%s'" % filters.get("status"))

    if filters.get("company"):
        condition_list.append("pos_opening_entry.company = '%s'" % filters.get("company"))

    if condition_list:
        conditions = "where " + " and ".join(condition_list)
    else:
        today = datetime.datetime.today().date()
        date_str = today.strftime('%Y-%m-%d')
        conditions ="where pos_opening_entry.posting_date=" + date_str

    item_results = frappe.db.sql(
        """select pos_opening_entry.posting_date as opening_date, pos_opening_entry.pos_profile, pos_opening_entry.period_end_date,
         pos_opening_entry.status, pos_opening_entry.name as opening_id, pos_opening_entry.pos_closing_entry as closing_id, pos_closing_entry.posting_date as closing_date
        from `tabPOS Opening Entry` pos_opening_entry left join `tabPOS Closing Entry` pos_closing_entry ON pos_opening_entry.name=pos_closing_entry.pos_opening_entry {}""".format(conditions), as_dict=1)

    return item_results
