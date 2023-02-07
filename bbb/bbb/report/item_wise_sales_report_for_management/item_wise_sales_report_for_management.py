# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns(filters)
    data = get_invoice_data(filters, columns)
    return columns, data


def get_columns(filters):
    """return columns"""
    columns = []
    invoice_type = filters.get('switch_invoice', "POS Invoice")
    # columns.append({"label": _("Date"), "fieldname": "posting_date", "fieldtype": "date", "width": 100})

    # if invoice_type == 'POS Invoice':
    #     columns.append(
    #         {"label": _("Invoice"), "fieldname": "invoice_name", "fieldtype": "Link", "options": "POS Invoice",
    #          "width": 170}),
    # else:
    #     columns.append(
    #         {"label": _("Invoice"), "fieldname": "invoice_name", "fieldtype": "Link", "options": "Sales Invoice",
    #          "width": 100}),

    columns = columns + [
        {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand",
         "width": 130},
        {"label": _("Item Category"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group",
         "width": 130},
        {"label": _("Product Code"), "fieldname": "item_code", "fieldtype": "Text", "options": "Item",
         "width": 150},
        {"label": _("Product Name"), "fieldname": "item_name", "fieldtype": "Text", "options": "Item",
         "width": 800},
        {"label": _("Total Sell Qty"), "fieldname": "total_sale_qty", "fieldtype": "Int", "width": 80},
        {"label": _("Current Stock"), "fieldname": "current_stock", "fieldtype": "Int", "width": 130},
        {"label": _("MRP Rate"), "fieldname": "mrp_rate", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
        {"label": _("MRP Value"), "fieldname": "mrp_value", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
        {"label": _("Sell Value"), "fieldname": "sell_value", "fieldtype": "Currency", "width": 90,
         "convertible": "rate", "options": "currency"},
        {"label": _("Profit/Loss"), "fieldname": "profit_loss", "fieldtype": "Currency", "width": 100,
         "convertible": "rate", "options": "currency"},
    ]

    return columns


def get_conditions(filters, columns):
    conditions = []
    pos_conditions = []
    if filters.get("from_date"):
        conditions.append("sales_invoice.posting_date >= '%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("sales_invoice.posting_date <= '%s'" % filters.get("to_date"))
    if filters.get("store"):
        conditions.append("sales_invoice.pos_profile = '%s'" % filters.get("store"))
    if filters.get("product_code"):
        conditions.append("sales_invoice_item.item_code = '%s'" % filters.get("product_code"))
    if filters.get("brand"):
        conditions.append("sales_invoice_item.brand = '%s'" % filters.get("brand"))
    if filters.get("item_group"):
        conditions.append("sales_invoice_item.item_group = '%s'" % filters.get("item_group"))
    if filters.get("served_by"):
        conditions.append("sales_invoice.served_by = '%s'" % filters.get("served_by"))

    if conditions:
        conditions = " and ".join(conditions)
        
    if filters.get("all_outlet"):
        pos_profile_list = frappe.db.get_list('POS Profile', {'company': filters.get('company')}, 'name')
        for pos_profile in pos_profile_list:
            columns.append({"label": _(pos_profile.name), "fieldname": pos_profile.name, "fieldtype": "Link", "width": 120, "options": "POS Profile"})
            
    
    elif filters.get('outlet'):
        outlet_list = filters.get('outlet')
        for outlet in outlet_list:
            pos_conditions.append("sales_invoice.pos_profile = '%s'" % outlet)
            columns.append({"label": _(outlet), "fieldname": outlet, "fieldtype": "Int", "width": 120, "options": "POS Profile"})

    if pos_conditions:
        pos_conditions = " or ".join(pos_conditions)
        conditions += "and (" + pos_conditions + ")"

    return conditions


def get_invoice_data(filters, columns):
    conditions = get_conditions(filters, columns)
    invoice_type = filters.get('switch_invoice', "POS Invoice")
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.pos_profile, item.item_code, item.item_name, item.brand, item.item_group, item.buying_rate,
    			sales_invoice_item.qty as sales_qty, sales_invoice_item.price_list_rate as mrp_rate, sales_invoice_item.rate as selling_rate, 
    			sales_invoice_item.net_amount, sales_invoice_item.amount as sell_value, sales_invoice.set_warehouse as warehouse
    		from `tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s
    		""" % (invoice_type, invoice_type, conditions), as_dict=1)
    


    outlet_list = []
    if filters.get("all_outlet"):
        pos_profile_list = frappe.db.get_list('POS Profile', {'company': filters.get('company')}, 'name')
        for pos_profile in pos_profile_list:
            outlet_list.append(pos_profile.name)
    elif filters.get('outlet'):
        outlet_list = filters.get('outlet')

    final_invoice_data = []
    item_code_set = set()

    for query in query_result:
        if query['item_code'] in item_code_set:
            invoice_dict = next((d for d in final_invoice_data if query['item_code'] in d.values()), None)
            invoice_dict[query['pos_profile']] = query['sales_qty']
            invoice_dict['total_sale_qty'] += query['sales_qty']
            invoice_dict['mrp_value'] += (query['mrp_rate'] * query['sales_qty'])
            invoice_dict['sell_value'] += (query['selling_rate'] * query['sales_qty'])
            invoice_dict['profit_loss'] += (query['selling_rate'] * query['sales_qty']) - (query['buying_rate'] * query['sales_qty'])
                    
        else:
            item_code_set.add(query['item_code'])
            for outlet in outlet_list:
                current_stock = frappe.db.get_value('Bin', {'item_code': query['item_code'], 'warehouse' : query['warehouse']}, 'actual_qty')
                if outlet == query['pos_profile']:
                    query[query['pos_profile']] = query['sales_qty']
                else:
                    query[outlet] = '0'
                query['current_stock'] = current_stock
                
            query['total_sale_qty'] = query['sales_qty']
            query['mrp_value'] = (query['mrp_rate'] * query['sales_qty'])
            query['sell_value'] = (query['selling_rate'] * query['sales_qty'])
            query['profit_loss'] = (query['selling_rate'] * query['sales_qty']) - (query['buying_rate'] * query['sales_qty'])
            

        final_invoice_data.append(query)

        
        
        # for outlet in outlet_list:
        #     try:
        #         query[query['pos_profile']]= int(query['sales_qty'])
        #     except:
        #         query.update({outlet: 0})

    return final_invoice_data



def pos_profile_query(doctype, txt, searchfield, start, page_len, filters):
    user = frappe.session['user']
    company = filters.get(
        'company') or frappe.defaults.get_user_default('company')

    args = {
        'user': user,
        'start': start,
        'company': company,
        'page_len': page_len,
        'txt': '%%%s%%' % txt
    }

    pos_profile = frappe.db.sql("""select distinct(pf.name)
		from
			`tabPOS Profile` pf, `tabPOS Profile User` pfu
		where
			pfu.parent = pf.name and user = %(user)s and pf.company = %(company)s
			and (pf.name like %(txt)s)
			and pf.disabled = 0 limit %(start)s, %(page_len)s""", args, debug=0)

    return pos_profile

#
# def get_stock_ledger_entries(filters, items):
# 	item_conditions_sql = ""
# 	if items:
# 		item_conditions_sql = "and sle.item_code in ({})".format(
# 			", ".join(frappe.db.escape(i) for i in items)
# 		)
#
# 	sl_entries = frappe.db.sql(
# 		"""
# 		SELECT
# 			concat_ws(" ", posting_date, posting_time) AS date,
# 			item_code,
# 			warehouse,
# 			actual_qty,
# 			qty_after_transaction,
# 			incoming_rate,
# 			valuation_rate,
# 			stock_value,
# 			voucher_type,
# 			voucher_no,
# 			batch_no,
# 			serial_no,
# 			company,
# 			project,
# 			stock_value_difference
# 		FROM
# 			`tabStock Ledger Entry` sle
# 		WHERE
# 			company = %(company)s
# 				AND is_cancelled = 0 AND posting_date BETWEEN %(from_date)s AND %(to_date)s
# 				{sle_conditions}
# 				{item_conditions_sql}
# 		ORDER BY
# 			posting_date asc, posting_time asc, creation asc
# 		""".format(
# 			sle_conditions=get_sle_conditions(filters), item_conditions_sql=item_conditions_sql
# 		),
# 		filters,
# 		as_dict=1,
# 	)
#
# 	return sl_entries

