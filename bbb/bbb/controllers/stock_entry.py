import frappe

def update_on_submit(doc,method=None):
    if doc.outgoing_stock_entry:
        stock_entry = frappe.get_doc("Stock Entry",doc.outgoing_stock_entry)
        stock_entry.db_set("workflow_state","Completed")