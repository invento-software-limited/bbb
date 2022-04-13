import frappe


def after_insert(doc, method):
    # For Standard Selling
    if doc.standard_rate is None:
        item_price = frappe.new_doc('Item Price')
        item_price.item_code = doc.item_code
        item_price.price_list_rate = 0
        item_price.price_list = 'Standard Selling'
        item_price.selling = 1
        item_price.save()

    # For Standard Buying
    item_price = frappe.new_doc('Item Price')
    item_price.item_code = doc.item_code
    item_price.price_list_rate = doc.buying_rate if doc.buying_rate else 0
    item_price.price_list = 'Standard Buying'
    item_price.buying = 1
    item_price.save()


def on_update(doc, method):
    if doc.standard_rate:
        frappe.db.sql("""update `tabItem Price` set price_list_rate={} where item_code='{}' and selling=1""".format(
            doc.standard_rate, doc.item_code))

    if doc.buying_rate:
        frappe.db.sql(
            """update `tabItem Price` set price_list_rate={} where item_code='{}' and buying=1""".format(
                doc.buying_rate, doc.item_code))
