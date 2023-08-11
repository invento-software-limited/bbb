# Copyright (c) 2023, invento software limited and contributors
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
            "fieldname": "name",
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
            "width": 170,
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
    today = datetime.datetime.today().date()

    condition_list = []
    if filters.get("date"):
        condition_list.append("pos_opening_entry.posting_date >= '%s'" % filters.get("date"))
        condition_list.append("pos_opening_entry.posting_date <= '%s'" % filters.get("date"))

    if filters.get("pos_profile"):
        condition_list.append("pos_opening_entry.pos_profile = '%s'" % filters.get("pos_profile"))

    if filters.get("status"):
        condition_list.append("pos_opening_entry.status = '%s'" % filters.get("status"))

    if filters.get("company"):
        condition_list.append("pos_opening_entry.company = '%s'" % filters.get("company"))

    if condition_list:
        # conditions = "where " + " and ".join(condition_list)
        conditions = " and ".join(condition_list)
    else:
        date_str = today.strftime('%Y-%m-%d')
        conditions = "pos_opening_entry.posting_date=" + date_str

    query_results = frappe.db.sql(
        """select pos_profile.name, pos_opening_entry.posting_date as opening_date, pos_opening_entry.pos_profile, pos_opening_entry.period_end_date,
         pos_opening_entry.status, pos_opening_entry.name as opening_id, pos_closing_entry.name as closing_id, pos_closing_entry.posting_date as closing_date 
        from `tabPOS Profile` pos_profile left join `tabPOS Opening Entry` pos_opening_entry on pos_opening_entry.pos_profile=pos_profile.name 
        and {} left join `tabPOS Closing Entry` pos_closing_entry ON pos_opening_entry.name=pos_closing_entry.pos_opening_entry where 
        pos_profile.name!='Distribution' and pos_profile.name!='Test Location'""".format(conditions), as_dict=1)

    for result in query_results:
        if not result.get('opening_id'):
            opening_entry = check_opening_entry(result.get("name"), filters.get("date"))
            if opening_entry:
                result['opening_id'] = opening_entry[0].get('name')
                result['opening_date'] = opening_entry[0].get('posting_date')


                date_string = str(opening_entry[0].get('posting_date'))
                current_date_string= filters.get("date")
                date_format = "%Y-%m-%d"
                current_date = datetime.datetime.strptime(current_date_string, date_format)
                specific_date = datetime.datetime.strptime(date_string, date_format)

                # Calculate the difference in days
                days_difference = (current_date - specific_date).days

                # Print the result
                if days_difference == 1:
                    status = "Yesterday"
                else:
                    status = str(days_difference) + " days ago"
                result['status'] = "Open " + status

    # print(query_results)
    return query_results


def check_opening_entry(pos_profile, date):
    open_vouchers = frappe.db.get_all(
        "POS Opening Entry",
        filters={"pos_closing_entry": ["in", ["", None]], "docstatus": 1, "status":"Open", "pos_profile": pos_profile, "posting_date": ["<=", date]},
        fields=["name", "posting_date", "pos_profile", "status", "period_start_date"],
        order_by="period_start_date desc",
    )

    return open_vouchers
