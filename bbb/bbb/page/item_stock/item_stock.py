import frappe

@frappe.whitelist()
def get_item_stock_data(search_text=None):
    items = []

    if search_text:
        items_query = '''select bin.warehouse, bin.item_code, item.item_name, bin.actual_qty from `tabBin` bin
                inner join `tabItem` item on item.item_code = bin.item_code join `tabItem Barcode` barcode on 
                barcode.parent = bin.item_code where bin.item_code like "%{}%" or barcode.barcode = "{}" or
                item.item_name like "%{}%" or item.item_name like "%{}%"'''.format(search_text,search_text, search_text,
                                                                                   search_text,search_text.lower())

        items = frappe.db.sql(items_query, as_dict=1)

    return items