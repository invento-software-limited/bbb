import frappe
from frappe.utils import flt

def update_on_submit(doc,method=None):
    if doc.stock_created_from and doc.total_transfer_qty == doc.total_accepted_qty:
        stock_entry = frappe.get_doc("Stock Entry",doc.stock_created_from)
        stock_entry.db_set("workflow_state","Completed")
        
def update_validate(doc,method=None):
    tqy = 0
    aqy = 0
    for item in doc.items:
        if item.get("qty"):
            aqy += item.get("qty")
        if item.get("transfer_qty_from_stock_distribution"):
            tqy += item.get("transfer_qty_from_stock_distribution")
            
    doc.total_transfer_qty = tqy
    doc.total_accepted_qty = aqy
    
@frappe.whitelist()
def make_stock_entry(name):
    stock_entry = frappe.get_doc("Stock Entry",name)
    items = []
    for item in stock_entry.items:
        if item.get("transfer_qty_from_stock_distribution") > item.get("qty"):
            item_dict = {
                "item_code" : item.get("item_code"),
                "transfer_qty_from_stock_distribution" : flt(item.get("transfer_qty_from_stock_distribution")) - flt(item.get("qty")),
                "qty" : flt(item.get("transfer_qty_from_stock_distribution")) - flt(item.get("qty")),
                "transfer_qty" : flt(item.get("transfer_qty_from_stock_distribution")) - flt(item.get("qty")),
                "s_warehouse" : item.get("s_warehouse"),
                "t_warehouse" : item.get("t_warehouse"),
                "conversion_factor" : item.get("conversion_factor"),
                "uom" : item.get("uom")
            }
            items.append(item_dict)
    return items