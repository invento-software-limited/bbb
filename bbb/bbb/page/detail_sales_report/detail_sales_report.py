# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from datetime import datetime
import time
from frappe.utils import get_time


def execute(filters=None):
    columns, data = get_columns(filters), demo_data
    data = data + get_invoice_data(filters)
    return columns, data


def get_columns(filters):
    """return columns"""
    invoice_type = filters.get('switch_invoice', "Sales Invoice")
    columns = list()
    columns.append({"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100})
    columns.append({"label": _("Posting Time"), "fieldname": "time", "fieldtype": "Time", "width": 75})

    if invoice_type == "Sales Invoice":
        columns.append({"label": _("Invoice No"), "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice",
                        "width": 400})
    else:
        columns.append({"label": _("Invoice No"), "fieldname": "name", "fieldtype": "Link", "options": "POS Invoice",
                        "width": 165})
    new_column = columns + [
        {"label": _("Customer Name"), "fieldname": "customer", "fieldtype": "Text", "width": 120},
        {"label": _("Branch"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 110},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Text", "width": 900},
        {"label": _("Special Discount"), "fieldname": "special_discount", "fieldtype": "Currency", "width": 150,
         "convertible": "rate", "options": "currency"},
        {"label": _("Rounding"), "fieldname": "rounding_adjustment", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("VAT"), "fieldname": "vat", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
        {"label": _("Served By"), "fieldname": "served_by", "fieldtype": "Link", "options": "Served By", "width": 150},
        {"label": _("Profit     / Loss"), "fieldname": "profit_loss", "fieldtype": "Currency", "width": 120,
         "convertible": "rate", "options": "currency"},
    ]

    return new_column


table = """
<table class="table table-bordered" style="">
    <thead>
        <tr>
            <th scope="col" >SL</th>
            <th scope="col">Invoice No/Customer</th>
            <th scope="col" colspan="6">Description</th>
            <th scope="col">Sales Person</th>
            <th scope="col">Store Name</th>
            <th scope="col">Special Discount</th>
            <th scope="col">Round</th>
            <th scope="col">VAT</th>
            <th scope="col">Total Amount</th>
            <th scope="col">Exchange</th>
            <th scope="col">Total</th>
        </tr>
    </thead>
</table>
"""

table_body = """
    <tr>
      <td scope="col" style="font-weight:300; font-size: 10px;padding:0.5rem !important; white-space: pre-wrap;!important" width="55%">{item_name}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{rate}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="5%">{qty}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{mrp}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{disc}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{total}</td>
    </tr>
"""

demo_data = [{'SL': 1, 'Sales Invoice': '0', 'pos_profile': '', 'description': table, 'special_discount': '',
              'rounding_adjustment': '', 'total_taxes_and_charges': ''}]


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("sales_invoice.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("sales_invoice.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("outlet"):
        conditions.append("sales_invoice.pos_profile = '%s'" % filters.get("outlet"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


@frappe.whitelist()
def get_invoice_data(filters):
    filters = json.loads(filters)
    conditions = get_conditions(filters)
    invoice_type = filters.get('switch_invoice', "Sales Invoice")
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.pos_profile, sales_invoice.total_taxes_and_charges as vat, sales_invoice.name, sales_invoice.posting_date, sales_invoice.posting_time, 
    			sales_invoice_item.price_list_rate as unit_price, sales_invoice_item.rate as selling_rate, item.standard_rate as mrp,
    			sales_invoice_item.qty as quantity, sales_invoice_item.item_name, item.standard_rate as mrp, sales_invoice.served_by,
    			(sales_invoice_item.qty * item.standard_rate) as mrp_total, ((sales_invoice_item.qty * sales_invoice_item.rate) - (sales_invoice_item.qty * item.buying_rate)) as profit_loss, 
    			(sales_invoice_item.qty * item.buying_rate) as buying_total, sales_invoice.customer_name, sales_invoice.customer_mobile_number,
    			((sales_invoice_item.qty * sales_invoice_item.discount_amount)) as discount, sales_invoice.set_warehouse, sales_invoice.special_note, 
    			(sales_invoice.total - sales_invoice.net_total) as special_discount, sales_invoice.total_qty, sales_invoice.return_against,
    			 sales_invoice_item.net_amount, sales_invoice_item.amount as total_amount, sales_invoice.customer_name, sales_invoice.is_return,
    			 sales_invoice.total, sales_invoice.rounded_total, sales_invoice.total_taxes_and_charges, sales_invoice.net_total, sales_invoice.rounding_adjustment
    		from `tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.posting_date, sales_invoice.posting_time asc 
    		""" % (invoice_type, invoice_type, conditions), as_dict=1)

    return_data = {}
    data = {}
    for result in query_result:
        # if result['is_return'] == 1:
        #     if return_data.get(result.get('name')):
        #         sales_data = return_data.get(result.get('name'))
        #         sales_data['mrp_total'] = sales_data['mrp_total'] + result['mrp_total']
        #         # sales_data['quantity'] = sales_data['quantity'] + result['quantity']
        #         sales_data['total_selling_rate'] = sales_data['total_selling_rate'] + result['selling_rate']
        #         sales_data['total_mrp_price'] = sales_data['total_mrp_price'] + result['mrp']
        #         sales_data['total_amount_'] = sales_data['total_amount_'] + result['total_amount']
        #         sales_data['total_discount'] = sales_data['total_discount'] + result['discount']
        #         sales_data['profit_loss'] = sales_data['profit_loss'] + result['profit_loss']
        #     else:
        #         result['total_selling_rate'] = result['selling_rate']
        #         result['total_discount'] = result['discount']
        #         result['total_amount_'] = result['total_amount']
        #         result['total_mrp_price'] = result['mrp']
        #         return_data[result.get('return_against')] = result

        if data.get(result.get('name')):
            sales_data = data.get(result.get('name'))

            if result['is_return'] == 0:
                sales_data['mrp_total'] = sales_data['mrp_total'] + result['mrp_total']
                # sales_data['quantity'] = sales_data['quantity'] + result['quantity']
                sales_data['total_selling_rate'] = sales_data['total_selling_rate'] + result['selling_rate']
                sales_data['total_mrp_price'] = sales_data['total_mrp_price'] + result['mrp']
                sales_data['total_amount_'] = sales_data['total_amount_'] + result['total_amount']
                sales_data['total_discount'] = sales_data['total_discount'] + result['discount']
            else:
                sales_data['mrp_total'] = ''
                # sales_data['quantity'] = ''
                sales_data['total_selling_rate'] = ''
                sales_data['total_mrp_price'] = ''
                sales_data['total_amount_'] = ''
                sales_data['total_discount'] = ''

            sales_data['profit_loss'] = sales_data['profit_loss'] + result['profit_loss']
            sales_data['total_item_qty'] = sales_data['total_item_qty'] + 1
        else:
            if result['special_note']:
                result['total_item_qty'] = 4
            else:
                result['total_item_qty'] = 3


            if result['is_return'] == 0:
                result['total_selling_rate'] = result['selling_rate']
                result['total_discount'] = result['discount']
                result['total_amount_'] = result['total_amount']
                result['total_mrp_price'] = result['mrp']
                result['total_return_amount'] = ''
                result['return_without_parent_invoice'] = False
            elif result['is_return'] == 1 and data.get(result['return_against'], None):
                result['total_selling_rate'] = ''
                result['total_discount'] = ''
                result['total_amount_'] = ''
                result['total_mrp_price'] = ''
                result['return_without_parent_invoice'] = True
                result['total_return_amount'] = result['rounded_total']
            elif result['is_return'] == 1:
                result['total_selling_rate'] = ''
                result['total_discount'] = ''
                result['total_amount_'] = ''
                result['total_mrp_price'] = ''
                result['return_without_parent_invoice'] = False
                result['total_return_amount'] = result['rounded_total']
            data[result.get('name')] = result

    # invoice_sales_data = {}
    # for index, invoice_name in enumerate(data):
    #     invoice_data = data[invoice_name]
    #     if invoice_data['is_return'] == 1:
    #         return_against = invoice_data['return_against']
    #         if return_against in invoice_sales_data:
    #             total_item_qty = invoice_data['total_item_qty']
    #             invoice_sales_data[return_against]['total_item_qty'] += total_item_qty
    #             invoice_sales_data[return_against]['return_data'] = invoice_data
    #
    #         else:
    #             total_item_qty = invoice_data['total_item_qty']
    #             invoice_sales_data[return_against]['return_without_parent_invoice'] = True
    #             invoice_sales_data[return_against]['return_data'] = invoice_data
    #     else:
    #         invoice_data['return_data'] = {}
    #         invoice_sales_data[invoice_name] = invoice_data

    # sales_data = {}
    # for index, result in enumerate(query_result):
    #     next_invoice = True
    #     invoice_name = result.get('name')
    #     try:
    #         next_invoice = query_result[index + 1]
    #         next_invoice = query_result[index + 1]['name']
    #     except:
    #         next_invoice = not next_invoice
    #
    #     invoice_without_total = {}
    #     invoice_without_total['name'] = invoice_name
    #     invoice_without_total['date'] = result.get('posting_date')
    #     invoice_without_total['time'] = result.get('posting_time')
    #     invoice_without_total['customer'] = result.get('customer_name')
    #     invoice_without_total['is_return'] = result.get('is_return')
    #     invoice_without_total['pos_profile'] = result.get('pos_profile')
    #     invoice_without_total['served_by'] = result.get('served_by')
    #     invoice_without_total['profit_loss'] = result.get('profit_loss')
    #     invoice_without_total['description'] = ''
    #     invoice_without_total['item_name'] = result.get('item_name')
    #     invoice_without_total['discount'] = result.get('discount')
    #     invoice_without_total['selling_rate'] = result.get('selling_rate')
    #     invoice_without_total['quantity'] = result.get('selling_rate')
    #     invoice_without_total['mrp'] = result.get('mrp')
    #     invoice_without_total['total_amount'] = result.get('total_amount')
    #     invoice_without_total['special_discount'] = result.get('special_discount')
    #     invoice_without_total['rounding_adjustment'] = result.get('rounding_adjustment')
    #     invoice_without_total['vat'] = result.get('total_taxes_and_charges')
    #     invoice_without_total['rounded_total'] = result.get('rounded_total')
    #
    #     invoice_with_total = {}
    #     if data.get(invoice_name, None):
    #         invoice_item_total = data.get(invoice_name)
    #         invoice_with_total['name'] = invoice_name
    #         invoice_with_total['date'] = result.get('posting_date')
    #         invoice_with_total['time'] = result.get('posting_time')
    #         invoice_without_total['is_return'] = result.get('is_return')
    #         invoice_with_total['customer'] = result.get('customer_name')
    #         invoice_with_total['pos_profile'] = result.get('pos_profile')
    #         invoice_with_total['served_by'] = result.get('served_by')
    #         invoice_with_total['profit_loss'] = result.get('profit_loss')
    #         invoice_with_total['description'] = ''
    #         invoice_with_total['item_name'] = 'Total'
    #         invoice_with_total['discount'] = invoice_item_total.get('total_discount')
    #         invoice_with_total['selling_rate'] = invoice_item_total.get('total_selling_rate')
    #         invoice_with_total['quantity'] = invoice_item_total.get('total_qty')
    #         invoice_with_total['mrp'] = invoice_item_total.get('total_mrp_price')
    #         invoice_with_total['total_amount'] = invoice_item_total.get('total_amount_')
    #         invoice_with_total['special_discount'] = result.get('special_discount')
    #         invoice_with_total['rounding_adjustment'] = result.get('rounding_adjustment')
    #         invoice_with_total['vat'] = result.get('total_taxes_and_charges')
    #         invoice_with_total['rounded_total'] = result.get('rounded_total')
    #
    #     if next_invoice and invoice_name == next_invoice:
    #         if sales_data.get(invoice_name):
    #             sales_data[invoice_name].append(invoice_without_total)
    #         else:
    #             sales_data[invoice_name] = [invoice_without_total]
    #     elif next_invoice and invoice_name != next_invoice:
    #         if sales_data.get(invoice_name):
    #             sales_data[invoice_name].append(invoice_without_total)
    #             sales_data[invoice_name].append(invoice_with_total)
    #         else:
    #             sales_data[invoice_name] = [invoice_without_total]
    #             sales_data[invoice_name].append(invoice_with_total)
    #     elif next_invoice == False:
    #         if sales_data.get(invoice_name):
    #             sales_data[invoice_name].append(invoice_without_total)
    #             sales_data[invoice_name].append(invoice_with_total)
    #
    #         else:
    #             sales_data[invoice_name] = [invoice_without_total]
    #             sales_data[invoice_name].append(invoice_without_total)

    sales_data = {}
    for index, result in enumerate(query_result):
        next_invoice = True
        invoice_name = result.get('name')
        try:
            next_invoice = query_result[index + 1]
            next_invoice = query_result[index + 1]['name']
        except:
            next_invoice = not next_invoice

        invoice_item_total = data.get(invoice_name)
        time_obj = datetime.strptime(f"{result['posting_time']}", '%H:%M:%S.%f').strftime("%I:%M %p")
        tr_first_row = f"""
            <tr>
                <th scope='row' rowspan='{invoice_item_total['total_item_qty']}'>{index + 1}</th>
                <td rowspan='{invoice_item_total['total_item_qty']}' class="text-center">{invoice_name}<br>{result['customer_name']} ({result['customer_mobile_number']})<br>{result['posting_date']} {time_obj}</td>
                <td>Name</td>
                <td>MRP</td>
                <td>Qty</td>
                <td>Unit Price</td>
                <td>Disc</td>
                <td>Total</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['served_by']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['set_warehouse']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['special_discount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['special_discount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['total_taxes_and_charges']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['total_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{invoice_item_total['total_return_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['rounded_total']}</td>
            </tr>

            <tr>
                <td>{result.get('item_name')}</td>
                <td>{result.get('mrp')}</td>
                <td>{result.get('quantity')}</td>
                <td>{result.get('selling_rate')}</td>
                <td>{result.get('discount')}</td>
                <td>{result.get('total_amount')}</td>
            </tr>
        """
        tr_return_with_header = f"""
            <tr>
                <th scope='row' rowspan='{invoice_item_total['total_item_qty']}'>{index + 1}</th>
                <td rowspan='{invoice_item_total['total_item_qty']}' class="text-center">{invoice_name}<br>{result['customer_name']} ({result['customer_mobile_number']})<br>{result['posting_date']} {time_obj}</td>
                <td>Name</td>
                <td>MRP</td>
                <td>Qty</td>
                <td>Unit Price</td>
                <td>Disc</td>
                <td>Total</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['served_by']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['set_warehouse']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['special_discount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['special_discount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['total_taxes_and_charges']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['total_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{invoice_item_total['total_return_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_qty']}'>{result['rounded_total']}</td>
            </tr>

            <tr>
                <td>{result.get('item_name')}</td>
                <td>{result.get('mrp')}</td>
                <td>{result.get('quantity')}</td>
                <td>{result.get('selling_rate')}</td>
                <td>{result.get('discount')}</td>
                <td>{result.get('total_amount')}</td>
            </tr>
        """

        tr_rowspan = f"""
            <tr>
                <td>{result.get('item_name')}</td>
                <td>{result.get('mrp')}</td>
                <td>{result.get('quantity')}</td>
                <td>{result.get('selling_rate')}</td>
                <td>{result.get('discount')}</td>
                <td>{result.get('total_amount')}</td>
            </tr>
        """

        tr_total_row = f"""
            <tr>
                <td colspan='2'>Total</td>     
                <td>{invoice_item_total.get('total_qty')}</td>     
                <td>{invoice_item_total.get('total_selling_rate')}</td>     
                <td>{invoice_item_total.get('total_discount')}</td>     
                <td>{invoice_item_total.get('total_amount_')}</td>   
            </tr>  
        """
        # tr_total_row = "<tr>"
        # tr_total_row +="<td colspan='2'>Total</td>"
        # tr_total_row +="<td>{}</td>".format(invoice_item_total.get('total_qty'))
        # tr_total_row +="<td>{}</td>".format(invoice_item_total.get('total_selling_rate'))
        # tr_total_row +="<td>{}</td>".format(invoice_item_total.get('total_discount'))
        # tr_total_row +="<td>{}</td>".format(invoice_item_total.get('total_amount_'))
        # tr_total_row +="</tr>"

        tr_special_note = f"""
            <tr style="background:#c3e0aad4">
                <td colspan='6'>Note: {result['special_note']}</td>  
            </tr>
        """
        tr_return_row = f"""
            <tr>
                <td>{result.get('item_name')}</td>
                <td>{result.get('mrp')}</td>
                <td>{result.get('quantity')}</td>
                <td>{result.get('selling_rate')}</td>
                <td>{result.get('discount')}</td>
                <td>{result.get('total_amount')}</td>
            </tr>
        """

        if next_invoice and invoice_name == next_invoice:
            if sales_data.get(invoice_name):
                sales_data[invoice_name].append(tr_rowspan)
            else:
                if result['is_return'] == 1 and invoice_item_total['return_without_parent_invoice'] == True:
                    sales_data[invoice_name] = [tr_return_with_header]
                else:
                    sales_data[invoice_name] = [tr_first_row]

        elif next_invoice and invoice_name != next_invoice:
            if sales_data.get(invoice_name):
                sales_data[invoice_name].append(tr_rowspan)
                if result['is_return'] == 0:
                    sales_data[invoice_name].append(tr_total_row)

                if result['special_note']:
                    sales_data[invoice_name].append(tr_special_note)
            else:
                if result['is_return'] == 1 and invoice_item_total['return_without_parent_invoice'] == True:
                    sales_data[invoice_name] = [tr_return_with_header]
                else:
                    sales_data[invoice_name] = [tr_first_row]
                    sales_data[invoice_name].append(tr_total_row)
                if result['special_note']:
                    sales_data[invoice_name].append(tr_special_note)

        elif next_invoice == False:
            if sales_data.get(invoice_name):
                sales_data[invoice_name].append(tr_rowspan)
                if result['is_return'] == 1:
                    sales_data[invoice_name].append(tr_rowspan)
                else:
                    sales_data[invoice_name].append(tr_total_row)
                if result['special_note']:
                    sales_data[invoice_name].append(tr_special_note)

            else:
                if result['is_return'] == 1 and invoice_item_total['return_without_parent_invoice'] == True:
                    sales_data[invoice_name] = [tr_rowspan]
                else:
                    sales_data[invoice_name] = [tr_first_row]
                    sales_data[invoice_name].append(tr_total_row)
                if result['special_note']:
                    sales_data[invoice_name].append(tr_special_note)

    return sales_data
