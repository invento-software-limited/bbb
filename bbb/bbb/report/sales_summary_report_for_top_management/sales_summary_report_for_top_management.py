# Copyright (c) 2013, Invento Bangladesh and contributors
# For license information, please see license.txt

# import frappe
# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe, erpnext
import copy
from frappe import _

def execute(filters=None, additional_table_columns=None, additional_query_columns=None):
    columns = get_columns()

    if not filters: filters = {}

    filters.update({"from_date": filters.get("date_range") and filters.get("date_range")[0],
                    "to_date": filters.get("date_range") and filters.get("date_range")[1]})

    item_list = get_items(filters, additional_query_columns)
    data = get_absolute_data(item_list)

    return columns, data


def get_absolute_data(invoice_items):
    invoice_list = get_invoice_list(invoice_items)
    branch_list = get_branches_list(invoice_list)

    for branch in branch_list:
        branch['total_discount'] = branch['discount'] + branch['special_discount']
        discount_rate = "{:.2f} %".format((branch['total_discount'] / branch['mrp_total']) * 100)
        branch['discount_rate'] = discount_rate
        print(branch)
        try:
            branch['sale_including_vat'] = branch.get('sale_excluding_vat', 0) + branch.get('invoice_tax_amount', 0)
            branch['basket_value'] = branch.get('sale_excluding_vat', 0) / branch.get('invoice_qty', 0)
        except:
            pass
    return branch_list

countable_values_dict = {
    'mrp_total': 0, 'discount': 0, 'special_discount': 0
}

def get_branches_list(invoice_list):
    branch_list_dict = {}
    countable_values_dict_ = {
        'base_net_total': 0,
        'net_total': 0,
        'grand_total': 0,
        'invoice_tax_amount': 0,
        'sale_excluding_vat': 0
    }
    countable_values_dict_.update(countable_values_dict)

    for invoice_item in invoice_list:
        if invoice_item['pos_profile'] not in branch_list_dict.keys():
            invoice_item['invoice_qty'] = 1
            branch_list_dict[invoice_item['pos_profile']] = invoice_item
        else:
            branch_invoice = branch_list_dict[invoice_item['pos_profile']]

            for key in countable_values_dict_.keys():
                if invoice_item.get(key, 0):
                    branch_invoice[key] += invoice_item.get(key, 0)

            branch_invoice['invoice_qty'] += 1

    return list(branch_list_dict.values())

def get_invoice_list(sales_invoice_items):
    invoice_list_dict = {}

    for sales_invoice_item in sales_invoice_items:
        if sales_invoice_item['parent'] not in invoice_list_dict.keys():
            invoice_list_dict[sales_invoice_item['parent']] = sales_invoice_item
        else:
            invoice = invoice_list_dict[sales_invoice_item['parent']]

            for key in countable_values_dict.keys():
                invoice[key] += sales_invoice_item[key]

    return list(invoice_list_dict.values())


def get_columns():
    """ Columns of Report Table"""
    return [
        {"label": _("Branch"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 150},
        {"label": _("Number Of Invoice"), "fieldname": "invoice_qty", "fieldtype": "Link", "options": "Sales Invoice",
         "width": 120},
        {"label": _("Basket Value"), "fieldname": "basket_value", "fieldtype": "Currency", "width": 120},
        {"label": _("MRP Total"), "fieldname": "mrp_total", "fieldtype": "Currency", "width": 120},
        # {"label": _("Selling Rate"), "fieldname": "selling_rate", "width": 125},
        {"label": _("Discount"), "fieldname": "discount", "fieldtype": "Currency", "width": 100},
        {"label": _("Special Discount"), "fieldname": "special_discount", "fieldtype": "Currency", "width": 150},
        {"label": _("Total Discount"), "fieldname": "total_discount", "fieldtype": "Currency", "width": 150},
        {"label": _("Discount Rate(%)"), "fieldname": "discount_rate", "fieldtype": "", "width": 150},

        {"label": _("Sell Excluding Vat"), "fieldname": "sale_excluding_vat", "fieldtype": "Currency", "width": 150},
        {"label": _("Vat"), "fieldname": "invoice_tax_amount", "fieldtype": "Currency", "width": 100},
        {"label": _("Sell Including Vat"), "fieldname": "sale_including_vat", "fieldtype": "Currency", "width": 150},

        {"label": _("Grand Total"), "fieldname": "grand_total", "fieldtype": "Currency", "width": 125},
    ]


def get_items(filters, additional_query_columns=None):
    conditions = get_conditions(filters)
    match_conditions = frappe.build_match_conditions("Sales Invoice")

    if match_conditions:
        match_conditions = " and {0} ".format(match_conditions)

    if additional_query_columns:
        additional_query_columns = ', ' + ', '.join(additional_query_columns)

    return frappe.db.sql("""
    		select
    			invoice_item.parent, invoice.grand_total,
                invoice.territory, invoice.net_total as sale_excluding_vat, invoice.total,
                
                invoice_item.base_net_amount, invoice_item.base_net_rate,
    			invoice.pos_profile, invoice_item.rate as selling_rate,
    			(invoice_item.qty * invoice_item.price_list_rate) as mrp_total,
    			((invoice_item.qty * invoice_item.price_list_rate) - (invoice_item.rate * invoice_item.qty)) as discount,
    			(invoice_item.amount - invoice_item.net_amount) as special_discount,
    			 invoice_item.net_amount, invoice_item.amount as total_amount,
    			 
    			 sales_tax.rate as invoice_tax_rate,
    			 sales_tax.tax_amount as invoice_tax_amount, sales_tax.total as invoice_tax_total {0}
    		from `tabSales Invoice` invoice, `tabSales Invoice Item` invoice_item LEFT JOIN `tabSales Taxes and Charges` sales_tax ON sales_tax.parent=invoice_item.parent
    		where invoice.name = invoice_item.parent 
    			and invoice.docstatus = 1 %s %s
    		order by invoice.posting_date desc, invoice_item.parent desc
    		""".format(additional_query_columns or '') % (conditions, match_conditions), filters, as_dict=1)


def get_conditions(filters):
    conditions = ""

    for opts in (("from_date", " and invoice.posting_date>=%(from_date)s"),
                 ("to_date", " and invoice.posting_date<=%(to_date)s")):

        if filters.get(opts[0]):
            conditions += opts[1]

    return conditions
