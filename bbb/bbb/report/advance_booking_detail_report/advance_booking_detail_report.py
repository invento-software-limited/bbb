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
        
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 500},
        {"label": _("MRP"), "fieldname": "mrp", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("MRP Total"), "fieldname": "mrp_total", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Data", "width": 55},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Item Disc Amount"), "fieldname": "item_discount_amount", "fieldtype": "Currency", "width": 110,
         "convertible": "rate", "options": "currency"},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        
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
        conditions.append("advance_booking.posting_date >= '%s'" %
                          filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("advance_booking.posting_date <= '%s'" %
                          filters.get("to_date"))
    if filters.get("outlet"):
        conditions.append("advance_booking.pos_profile = '%s'" %
                          filters.get("outlet"))

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
    	advance_booking.total,
    	advance_booking.discount_amount,
     	advance_booking.grand_total,
     	advance_booking.rounded_total,
     	advance_booking.total_advance,
     	advance_booking.outstanding_amount,
		advance_booking_item.item_name,
		advance_booking_item.rate,
		advance_booking_item.amount,
		advance_booking_item.qty,
		advance_booking_item.discount_amount as item_discount_amount,
		advance_booking_item.net_amount,
		advance_booking_item.price_list_rate as mrp
      	FROM `tabAdvance Booking` advance_booking join `tabAdvance Booking Item` advance_booking_item on advance_booking.name = advance_booking_item.parent
       	where advance_booking.docstatus = 1 and %s order by advance_booking.name""" % (conditions), as_dict=1)

    booking_id_list = []
    data = []
    for result in query_result:
        booking_id = result.get('name')
        if booking_id in booking_id_list:
            data.append({
				'item_name': result.get('item_name'),
				'mrp': result.get('mrp'),
				'qty': result.get('qty'),
				'mrp_total': float(result.get('qty')) * float(result.get('mrp')),
				'rate': result.get('rate'),
				'item_discount_amount': result.get('item_discount_amount'),
				'amount': result.get('amount')
			})
        else:
            data.append({
				'name': result.get('name'),
				'pos_profile': result.get('pos_profile'),
				'posting_date': result.get('posting_date'),
				'actual_service_date': result.get('actual_service_date'),
				'total_qty': result.get('total_qty'),
				'total': result.get('total'),
				'discount_amount': result.get('discount_amount'),
				'grand_total': result.get('grand_total'),
				'rounded_total': result.get('rounded_total'),
				'total_advance': result.get('total_advance'),
				'outstanding_amount': result.get('outstanding_amount'),

			})
            data.append({
				'item_name': result.get('item_name'),
				'mrp': result.get('mrp'),
				'qty': result.get('qty'),
				'mrp_total': float(result.get('qty', 0)) * float(result.get('mrp', 0),),
				'rate': result.get('rate'),
				'item_discount_amount': result.get('item_discount_amount'),
				'amount': result.get('amount')
			})
            booking_id_list.append(result.get('name'))

    return data
