import frappe


def on_submit(doc, method):
    if doc.grand_total > 0:
        frappe.db.set_value("Sales Invoice", doc.name, "grand_total", doc.grand_total - doc.rounding_adjustment)
    elif doc.grand_total < 0:
        frappe.db.set_value("Sales Invoice", doc.name, "grand_total", doc.grand_total - doc.rounding_adjustment)