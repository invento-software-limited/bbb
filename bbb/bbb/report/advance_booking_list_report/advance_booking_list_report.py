# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import copy


def execute(filters=None):
    columns, data = get_columns(), get_invoice_data(filters)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        # {"label": _("No"), "fieldname": "serial_no", "fieldtype": "Text", "width": 100},
        {"label": _("Booking Id"), "fieldname": "name", "fieldtype": "Link", "options": "Advance Booking",
         "width": 180},
        {"label": _("Outlet"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile",
         "width": 150},
        {"label": _("Posting Date"), "fieldname": "posting_date",
         "fieldtype": "Date", "width": 110},
        {"label": _("Service Date"), "fieldname": "actual_service_date",
         "fieldtype": "Date", "width": 110},
        {"label": _("Status"), "fieldname": "status",
         "fieldtype": "Data", "width": 130},
        {"label": _("Billing Status"), "fieldname": "billing_status",
         "fieldtype": "Data", "width": 110},
        {"label": _("Total Qty"), "fieldname": "total_qty",
         "fieldtype": "Int", "width": 85},
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Discount"), "fieldname": "discount_amount", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 110,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rounded Total"), "fieldname": "rounded_total", "fieldtype": "Currency", "width": 115,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Advance"), "fieldname": "total_advance", "fieldtype": "Currency", "width": 115,
         "convertible": "rate", "options": "currency"},
        {"label": _("Total Due"), "fieldname": "outstanding_amount", "fieldtype": "Currency", "width": 110,
         "convertible": "rate", "options": "currency"},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("advance_booking.actual_service_date >= '%s'" %
                          filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("advance_booking.actual_service_date <= '%s'" %
                          filters.get("to_date"))
        
    if filters.get("billing_status"):
        conditions.append("advance_booking.billing_status = '%s'" %
                          filters.get("billing_status"))
        
    if filters.get("status"):
        conditions.append("advance_booking.status = '%s'" %
                          filters.get("status"))

    if filters.get("outlet"):
        conditions.append("advance_booking.pos_profile = '%s'" %filters.get("outlet"))
        
    if filters.get("company"):
        conditions.append("advance_booking.company = '%s'" %
                          filters.get("company"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql(""" SELECT advance_booking.pos_profile,
       	advance_booking.name,
    	advance_booking.pos_profile,
    	advance_booking.posting_date,
    	advance_booking.actual_service_date,
    	advance_booking.total_qty,
    	advance_booking.billing_status,
    	advance_booking.status,
    	advance_booking.total,
    	advance_booking.discount_amount,
     	advance_booking.grand_total,
     	advance_booking.rounded_total,
     	advance_booking.total_advance,
     	advance_booking.outstanding_amount
      	FROM `tabAdvance Booking` advance_booking where advance_booking.docstatus = 1 and %s order by advance_booking.name""" % (conditions), as_dict=1)

    return query_result
