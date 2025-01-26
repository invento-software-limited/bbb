import frappe


def after_insert_or_on_update(doc, method):
    item = frappe.get_doc('Item', {'item_code': doc.item_code})
    if doc.selling == 1 and doc.price_list_rate != item.standard_rate:
        item.standard_rate = doc.price_list_rate
        item.save()

    if doc.buying == 1 and doc.price_list_rate != item.buying_rate:
        item.buying_rate = doc.price_list_rate
        item.save()
