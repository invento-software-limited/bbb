# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from bbb.bbb.doctype.stock_distribution.stock_distribution import caluclate_warehouse_percentage_wise_distribution


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_columns(filters):
    """return columns"""
    columns = [
        {"label": _("Stock Distribution"), "fieldname": "name", "fieldtype": "Link","options" : "Stock Distribution", "width": 120},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": _("Purchase Order"), "fieldname": "purchase_order", "fieldtype": "Link","options" : "Purchase Order", "width": 180},
        {"label": _("Supplier"), "fieldname": "supplier", "fieldtype": "Link","options" : "Supplier", "width": 120}
        
    ]
    if filters.get("view") == "Summary":
        columns.append({"label": _("Purchase Receipt"), "fieldname": "against_purchase_receipt", "fieldtype": "Link","options" : "Purchase Receipt", "width": 150})
        columns.append({"label": _("Total QTY"), "fieldname": "total_qty", "fieldtype": "Float", "width": 120})
        columns.append({"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120})
    else:
        columns.append({"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link","options" : "Item", "width": 120})
        columns.append({"label": _("Source Warehouse"), "fieldname": "source", "fieldtype": "Link","options" : "Warehouse", "width": 120})
        conditions = get_conditions(filters)
        query = frappe.db.sql("""select sd.name as name from `tabStock Distribution` as sd 
                                        where sd.docstatus = 1 {} order by sd.creation desc""".format(conditions),as_dict=1)
        warehouses = []
        for x in query:
            sd = frappe.get_doc("Stock Distribution" , x.get("name"))
            for y in sd.outlet_selection_table:
                label = y.get("warehouse")
                warehouses.append(label)
        for w in set(warehouses):
            filedname = w.lower().replace(" ","_").replace("-","&")
            columns.append({"fieldname": filedname, 'label': w, "expwidth": 13, "width": 150})
    return columns



def get_data(filters):
    conditions = get_conditions(filters)
    if filters.get("view") == "Summary":
        query = frappe.db.sql("""select sd.name as name, sd.purchase_order,sd.against_purchase_receipt,
                                sd.posting_date,sd.supplier,sd.total_qty,se.workflow_state as status
                                        from `tabStock Distribution` as sd left join `tabStock Entry` as se on se.stock_distribution = sd.name
                                            where sd.docstatus = 1 {} group by sd.name order by sd.creation desc""".format(conditions),as_dict=1)
        return query
    else:
        data = []
        
        query = frappe.db.sql("""select sd.name as name 
                                        from `tabStock Distribution` as sd where sd.docstatus > -1 {} order by sd.creation desc""".format(conditions),as_dict=1)
        for x in query:
            sd = frappe.get_doc("Stock Distribution" , x.get("name"))
            calculate_items = caluclate_warehouse_percentage_wise_distribution(sd.purchase_distribution_items,sd.outlet_selection_table,"Yes")
            for y in calculate_items:
                y["name"] = sd.name
                y["purchase_order"] = sd.purchase_order
                y["supplier"] = sd.supplier
                y["posting_date"] = sd.posting_date
                data.append(y)
            data.append({"name" : ""})
        
        return data

def get_conditions(filters):
    if not filters: filters = {}
    conditions = ""
    if filters.get("from_date"):
        conditions += " and sd.posting_date >= '{}'".format(filters.get("from_date"))
    if filters.get("to_date"):
        conditions += " and sd.posting_date <= '{}'".format(filters.get("to_date"))
    if filters.get("purchase_order"):
        conditions += " and sd.purchase_order = '{}'".format(filters.get("purchase_order"))
    if filters.get("purchase_receipt"):
        conditions += " and sd.against_purchase_receipt = '{}'".format(filters.get("purchase_receipt"))
    if filters.get("company"):
        conditions += " and sd.company = '{}'".format(filters.get("company"))
    if filters.get("supplier"):
        conditions += " and sd.supplier = '{}'".format(filters.get("supplier"))
    if filters.get("stock_distribution"):
        conditions += " and sd.name = '{}'".format(filters.get("stock_distribution"))
    return conditions