# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_customer_data(filters)
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Voucher No"), "fieldname": "name", "fieldtype": "Text", "options": "POS Invoice", "width": 170},
        {"label": _("Customer"), "fieldname": "customer_name", "fieldtype": "Link", "options": "Customer",
         "width": 100},
        {"label": _("Mobile No."), "fieldname": "customer_mobile_number", "fieldtype": "Text", "width": 150},
        {"label": _("Outlet"), "fieldname": "pos_profile", "fieldtype": "Text", "width": 120},
        {"label": _("Source"), "fieldname": "total_invoice", "fieldtype": "Int", "width": 80},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Text", "width": 550},
        {"label": _("Qty"), "fieldname": "qty", "fieldtype": "Int", "width": 60},
        {"label": _("  "), "fieldname": "click_here", "fieldtype": "Text", "width": 120},
    ]
    return columns


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("pos_invoice.posting_date <= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("pos_invoice.posting_date >= '%s'" % filters.get("to_date"))

    if filters.get("company"):
        conditions.append("pos_invoice.company = '%s'" % filters.get("company"))

    if filters.get("pos_profile"):
        conditions.append("pos_invoice.pos_profile = '%s'" % filters.get("pos_profile"))

    conditions.append("pos_invoice.docstatus = 1")

    return " and ".join(conditions)


def get_customer_data(filters):
    conditions = get_conditions(filters)
    invoice_sql = """select pos_invoice.name, pos_invoice.customer_name, pos_invoice.customer_mobile_number, pos_invoice.pos_profile, pos_invoice.name as click_here from `tabPOS Invoice` pos_invoice where %s order by pos_invoice.name""" % conditions
    pos_invoices = frappe.db.sql(invoice_sql, as_dict=1)
    customer_data = []
    for invoice in pos_invoices:
        if filters.get('type') == 'Yesterday':
            feedback_status = frappe.db.get_value('Customer Feedback', {'voucher_no': invoice.get('name'), 'status': 'Customer Feedback Collected'}, 'name')
            if feedback_status:
                invoice['click_here'] = 'feedback_received'

        elif filters.get('type') == 'Follow-Up 1 Month':
            feedback_status = frappe.db.get_value('Customer Feedback', {'voucher_no': invoice.get('name'),
                                                                        'status': 'Completed'},
                                                  'name')
            if feedback_status:
                invoice['click_here'] = 'feedback_received'

        customer_data.append(invoice)
        item_sql = """select pos_invoice_item.item_name, pos_invoice_item.qty from `tabPOS Invoice Item` pos_invoice_item where pos_invoice_item.parent='%s' """ % invoice.get(
            'name')
        pos_invoice_items = frappe.db.sql(item_sql, as_dict=1)
        for pos_invoice_item in pos_invoice_items:
            customer_data.append(pos_invoice_item)
    return customer_data


@frappe.whitelist()
def create_new_doc(invoice_name):
    doc = frappe.new_doc("Customer Feedback")
    doc.voucher_no = invoice_name
    doc.insert()
    return doc.name


