# Copyright (c) 2013, Invento Bangladesh and contributors
# For license information, please see license.txt

# import frappe
# Copyright (c) 2013, Invento Software Limited and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe, erpnext
import copy
from frappe import _
from frappe.utils import flt
from frappe.model.meta import get_field_precision
from frappe.utils.xlsxutils import handle_html
from erpnext.accounts.report.sales_register.sales_register import get_mode_of_payments


def execute(filters=None, additional_table_columns=None, additional_query_columns=None):
    columns = get_columns()

    if not filters: filters = {}

    filters.update({"from_date": filters.get("date_range") and filters.get("date_range")[0],
                    "to_date": filters.get("date_range") and filters.get("date_range")[1]})

    item_list = get_items(filters, additional_query_columns)
    data = get_absolute_data(item_list)

    return columns, item_list


def get_absolute_data(data):
    previous_object = {}
    object_ = {}
    blank_object = {}
    fields = ['parent', 'posting_date', 'posting_time', 'contact_mobile', 'customer', 'pos_profile', 'served_by', 'grand_total']

    for i, object in enumerate(data):
        temp_obj = copy.deepcopy(object)

        if previous_object and previous_object.get('parent') != temp_obj.get('parent'):
            object_ = {}

        # for attr, value in object.items():
        for field in fields:
            blank_object[field] = ''

            if object_ and object_.get(field) == object.get(field):
                data[i][field] = ''
            else:
                object_[field] = object.get(field)

        previous_object = copy.deepcopy(temp_obj)

    return data


def get_columns():
    """ Columns of Report Table"""
    return [
        {"label": _("Invoice Date"), "fieldname": "posting_date", "width": 100},
        {"label": _("Invoice Time"), "fieldname": "posting_time", "width": 100},
        {"label": _("Invoice No."), "fieldname": "parent", "fieldtype": "Link", "options": "Sales Invoice",
         "width": 200},
        {"label": _("Customer"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 150},
        {"label": _("Mobile Number"), "fieldname": "contact_mobile", "width": 120},
        {"label": _("Branch"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 175},
        # {"label": _("Reference"), "fieldname": "reference", "width": 125},
        {"label": _("Served By"), "fieldname": "served_by", "width": 125},
        {"label": _("Product Name"), "fieldname": "item_name", "width": 125},
        {"label": _("Unit Price"), "fieldname": "unit_price", "width": 125},
        {"label": _("Quantity"), "fieldname": "quantity", "width": 125},
        {"label": _("MRP Total"), "fieldname": "mrp_total", "width": 125},
        {"label": _("Selling Rate"), "fieldname": "selling_rate", "width": 125},
        {"label": _("Discount"), "fieldname": "discount", "width": 125},
        {"label": _("Total Amount"), "fieldname": "total_amount", "width": 125},
        # {"label": _("Vat"), "fieldname": "vat", "width": 125},
        {"label": _("Special Discount"), "fieldname": "special_discount", "width": 125},
        {"label": _("Grand Total"), "fieldname": "grand_total", "width": 125},
        # {"label": _("Mode of Payment"), "fieldname": "mode_of_payment", "width":120},
        # {"label": _("Territory"), "fieldname": "territory", "fieldtype": "Link", "options": "Territory", "width":80 },
        # {"label": _("Company"), "fieldname": "company" , "fieldtype": "Link", "options": "Company", "width": 100},
        # {"label": _("Stock Qty"), "fieldname": "stock_qty", "fieldtype":"Float", "width":120},
        # {"label": _("Stock UOM"), "fieldname": "stock_uom", "field_type": "Float", "width":100},
        # {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width":120},
        # {"label": _("Amount"), "fieldname": "company", "fieldtype": "Currency", "width":120}
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
    			`tabSales Invoice Item`.name, `tabSales Invoice Item`.parent, 
    			`tabSales Invoice`.contact_mobile, `tabSales Invoice`.grand_total,
    			`tabSales Invoice`.served_by as served_by, 
    			`tabSales Invoice`.posting_date, `tabSales Invoice`.posting_time,
    			`tabSales Invoice`.customer, `tabSales Invoice`.customer, 

    			`tabSales Invoice`.debit_to, 
    			`tabSales Invoice`.remarks, `tabSales Invoice`.project,
                `tabSales Invoice`.territory,  `tabSales Invoice`.base_net_total,

    			`tabSales Invoice Item`.item_group, `tabSales Invoice Item`.description, `tabSales Invoice Item`.sales_order,
    			`tabSales Invoice Item`.delivery_note, `tabSales Invoice Item`.income_account,
                `tabSales Invoice Item`.cost_center, `tabSales Invoice Item`.base_net_amount,
                `tabSales Invoice`.update_stock, `tabSales Invoice Item`.uom, `tabSales Invoice Item`.stock_qty,
                `tabSales Invoice Item`.stock_uom, `tabSales Invoice Item`.base_net_rate,

    			`tabSales Invoice Item`.item_code, `tabSales Invoice Item`.item_name,
    			`tabSales Invoice Item`.price_list_rate as unit_price, `tabSales Invoice Item`.rate as selling_rate,
    			`tabSales Invoice Item`.qty as quantity,
    			(`tabSales Invoice Item`.qty * `tabSales Invoice Item`.price_list_rate) as mrp_total,
    			((`tabSales Invoice Item`.qty * `tabSales Invoice Item`.price_list_rate) - (`tabSales Invoice Item`.rate * `tabSales Invoice Item`.qty)) as discount,
    			(`tabSales Invoice Item`.amount - `tabSales Invoice Item`.net_amount) as special_discount,
    			 `tabSales Invoice Item`.net_amount, `tabSales Invoice Item`.amount as total_amount, `tabSales Invoice`.customer_name {0}
    		from `tabSales Invoice`, `tabSales Invoice Item`
    		where `tabSales Invoice`.name = `tabSales Invoice Item`.parent
    			and `tabSales Invoice`.docstatus = 1 %s %s
    		order by `tabSales Invoice`.posting_date desc, `tabSales Invoice Item`.parent desc
    		""".format(additional_query_columns or '') % (conditions, match_conditions), filters, as_dict=1)


def get_conditions(filters):
    conditions = ""

    for opts in (("company", " and company=%(company)s"),
                 ("customer", " and `tabSales Invoice`.customer = %(customer)s"),
                 ("patient_concern", " and `tabSales Invoice`.patient_concern = %(patient_concern)s"),
                 ("age", " and `tabSales Invoice`.age <= %(age)s"),
                 ("item_code", " and `tabSales Invoice Item`.item_code = %(item_code)s"),
                 ("from_date", " and `tabSales Invoice`.posting_date>=%(from_date)s"),
                 ("to_date", " and `tabSales Invoice`.posting_date<=%(to_date)s")):

        if filters.get(opts[0]):
            conditions += opts[1]

    if filters.get("mode_of_payment"):
        conditions += """ and exists(select name from `tabSales Invoice Payment`
			where parent=`tabSales Invoice`.name
				and ifnull(`tabSales Invoice Payment`.mode_of_payment, '') = %(mode_of_payment)s)"""

    if filters.get("warehouse"):
        conditions += """ and exists(select name from `tabSales Invoice Item`
			 where parent=`tabSales Invoice`.name
			 	and ifnull(`tabSales Invoice Item`.warehouse, '') = %(warehouse)s)"""

    if filters.get("brand"):
        conditions += """ and exists(select name from `tabSales Invoice Item`
			 where parent=`tabSales Invoice`.name
			 	and ifnull(`tabSales Invoice Item`.brand, '') = %(brand)s)"""

    if filters.get("item_group"):
        conditions += """ and exists(select name from `tabSales Invoice Item`
			 where parent=`tabSales Invoice`.name
			 	and ifnull(`tabSales Invoice Item`.item_group, '') = %(item_group)s)"""

    if filters.get("pos_profile"): conditions += " and `tabSales Invoice`.pos_profile = %(pos_profile)s"
    #
    # if filters.get("doctors"): conditions += " and `tabSales Invoice Item`.doctors = %(doctors)s"

    if filters.get("served_by"): conditions += " and `tabSales Invoice`.served_by = %(served_by)s"

    # if filters.get("reference"): conditions += " and `tabSales Invoice Item`.reference = %(reference)s"

    if filters.get("sale_type"): conditions += " and `tabSales Invoice Item`.sale_type = %(sale_type)s"

    return conditions
