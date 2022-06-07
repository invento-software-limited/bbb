import frappe

@frappe.whitelist()
def get_item_stock_data(item_code=None, warehouse=None):
    items = []

    items_query = """select bin.warehouse, bin.item_code, item.item_name, bin.actual_qty from `tabBin` bin
            inner join `tabItem` item on item.item_code = bin.item_code"""

    if item_code:
        items_query += """ where bin.item_code = '%s'""" % item_code
    if warehouse and "where" in items_query:
        items_query += """ and bin.warehouse = '%s'""" % warehouse
    elif warehouse:
        items_query += """ where bin.warehouse = '%s'""" % warehouse

    if item_code:
        items = frappe.db.sql(items_query, as_dict=1)

    return items