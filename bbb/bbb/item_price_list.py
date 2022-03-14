import frappe


def validate(doc, method):
    if doc.selling == 1:
        frappe.db.sql(
            """update `tabItem` set standard_rate={} where item_code='{}'""".format(doc.price_list_rate, doc.item_code))

    if doc.buying == 1:
        frappe.db.sql(
            """update `tabItem` set buying_rate={} where item_code='{}'""".format(doc.price_list_rate, doc.item_code))
