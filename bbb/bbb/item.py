import frappe


def validate(doc, method):
    selling_price = frappe.db.sql(
        '''select item_code from `tabItem Price` where item_code='{}' and selling=1'''.format(doc.item_code))
    buying_price = frappe.db.sql(
        '''select item_code from `tabItem Price` where item_code='{}' and buying=1'''.format(doc.item_code))

    if selling_price:
        frappe.db.sql("""update `tabItem Price` set price_list_rate={} where item_code='{}' and selling=1""".format(
            doc.standard_rate, doc.item_code))
    else:
        try:
            item_price = frappe.new_doc('Item Price')
            item_price.item_code = doc.item_code
            item_price.price_list_rate = doc.standard_rate if doc.standard_rate else 0
            item_price.price_list = 'Standard Selling'
            item_price.selling = 1
            item_price.save()
        except:
            pass

    if buying_price:
        frappe.db.sql(
            """update `tabItem Price` set price_list_rate={} where item_code='{}' and buying=1""".format(
                doc.buying_rate,
                doc.item_code))
    else:
        try:
            item_price = frappe.new_doc('Item Price')
            item_price.item_code = doc.item_code
            item_price.price_list_rate = doc.buying_rate if doc.buying_rate else 0
            item_price.price_list = 'Standard Buying'
            item_price.buying = 1
            item_price.save()
        except:
            pass
