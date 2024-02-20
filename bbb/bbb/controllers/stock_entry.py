import frappe

def update_on_submit(doc,method=None):
    if doc.outgoing_stock_entry:
        stock_entry = frappe.get_doc("Stock Entry",doc.outgoing_stock_entry)
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