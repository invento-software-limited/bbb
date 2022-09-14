# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import json
from datetime import datetime
import time
from frappe.utils import get_time


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
    			sales_invoice_item.price_list_rate as unit_price, sales_invoice_item.rate as selling_rate, item.standard_rate as mrp, sales_invoice_item.idx,
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

    data = {}
    for index, result in enumerate(query_result):
        if data.get(result.get('name'), None):
            sales_data = data.get(result.get('name'))
            if result['is_return'] == 0:
                sales_data['mrp_total_price'] = sales_data['mrp_total_price'] + result['mrp_total']
                # sales_data['quantity'] = sales_data['quantity'] + result['quantity']
                sales_data['total_selling_rate'] = sales_data['total_selling_rate'] + result['selling_rate']
                # sales_data['total_mrp_price'] = sales_data['total_mrp_price'] + result['mrp']
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
            sales_data['total_item_row'] = sales_data['total_item_row'] + 1

        elif data.get(result['return_against'], None):
            sales_data = data.get(result['return_against'])

            if sales_data['exchange_item'] < 0:
                sales_data['total_item_row'] = sales_data['total_item_row'] + 1
                sales_data['exchange_item'] = result['idx']
                if result['special_note']:
                    sales_data['total_item_row'] = sales_data['total_item_row'] + 1

            # if result['special_note']:
            #     sales_data['total_item_row'] = sales_data['total_item_row'] + 2
            # else:
            sales_data['total_item_row'] = sales_data['total_item_row'] + 1
            sales_data['total_return_amount'] = result['rounded_total']

        else:
            result['exchange_item'] = -1
            # if result['is_return'] < 0:
            #     result['exchange_item'] = result['idx']
            #
            # if result['special_note'] and result['is_return'] == 0:
            #     result['total_item_row'] = 4
            # elif result['special_note'] and result['is_return'] == 1 or result['is_return'] == 0:
            #     result['total_item_row'] = 3
            # else:
            #     result['total_item_row'] = 2

            if result['is_return'] < 0:
                result['exchange_item'] = result['idx']

            if result['special_note']:
                result['total_item_row'] = 4
            else:
                result['total_item_row'] = 3

            if result['is_return'] == 0:
                result['total_selling_rate'] = result['selling_rate']
                result['total_discount'] = result['discount']
                result['total_amount_'] = result['total_amount']
                result['total_mrp_price'] = result['mrp']
                result['total_return_amount'] = ''
            else:
                result['total_selling_rate'] = ''
                result['total_discount'] = ''
                result['total_amount_'] = ''
                result['total_mrp_price'] = ''
                result['total_return_amount'] = result['rounded_total']
            result['mrp_total_price'] = result['mrp_total']
            data[result.get('name')] = result

    sales_data = {}
    for index, result in enumerate(query_result):
        sl_number = len(sales_data) + 1
        next_invoice = True
        invoice_name = result.get('name')
        try:
            next_invoice = query_result[index + 1]
            next_invoice = query_result[index + 1]['name']
        except:
            next_invoice = not next_invoice

        invoice_item_total = data.get(invoice_name)
        if invoice_item_total is None:
            invoice_item_total = data.get(result['return_against'])

        time_obj = datetime.strptime(f"{result['posting_time']}", '%H:%M:%S.%f').strftime("%I:%M %p")
        style = 'style="background:#ffff0085"' if result['special_discount'] > 0 else ''
        tr_first_row = f"""
            <tr>
                <th scope='row' rowspan='{invoice_item_total['total_item_row']}'>{sl_number}</th>
                <td rowspan='{invoice_item_total['total_item_row']}' class="text-center">{invoice_name}<br>{result['customer_name']} ({result['customer_mobile_number']})<br>{result['posting_date']} {time_obj}</td>
                <td>Name</td>
                <td>MRP</td>
                <td>Qty</td>
                <td>MRP Total</td>
                <td>Disc</td>
                <td>Total</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['served_by']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['set_warehouse']}</td>
                <td {style} rowspan='{invoice_item_total['total_item_row']}'>{result['special_discount']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['rounding_adjustment']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['total_taxes_and_charges']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['net_total']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{invoice_item_total['total_return_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['rounded_total']}</td>
            </tr>

            <tr>
                <td>{result.get('item_name')}</td>
                <td>{result.get('mrp')}</td>
                <td>{result.get('quantity')}</td>
                <td>{result.get('mrp_total')}</td>
                <td>{result.get('discount')}</td>
                <td>{result.get('total_amount')}</td>
            </tr>
        """

        tr_return_with_header = f"""
            <tr>
                <th scope='row' rowspan='{invoice_item_total['total_item_row']}'>{sl_number}</th>
                <td rowspan='{invoice_item_total['total_item_row']}' class="text-center">{invoice_name}<br>{result['customer_name']} ({result['customer_mobile_number']})<br>{result['posting_date']} {time_obj}</td>
                <td>Name</td>
                <td>MRP</td>
                <td>Qty</td>
                <td>MRP Total</td>
                <td>Disc</td>
                <td>Total</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['served_by']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['set_warehouse']}</td>
                <td {style} rowspan='{invoice_item_total['total_item_row']}'>{result['special_discount']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{invoice_item_total['rounding_adjustment']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['total_taxes_and_charges']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['total_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{invoice_item_total['total_return_amount']}</td>
                <td rowspan='{invoice_item_total['total_item_row']}'>{result['rounded_total']}</td>
            </tr>
            <tr>
                <td colspan='6' class="font-weight-bold text-center" style="background:#c3e0aad4">Exchange Product List</td>
            </tr>
            <tr>
                <td>{result.get('item_name')}</td>
                <td style="background:#ffff0085">{result.get('mrp')}</td>
                <td style="background:#ffff0085">{result.get('quantity')}</td>
                <td style="background:#ffff0085">{result.get('selling_rate')}</td>
                <td style="background:#ffff0085">{result.get('discount')}</td>
                <td style="background:#ffff0085">{result.get('total_amount')}</td>
            </tr>
        """

        tr_rowspan = f"""
            <tr>
                <td>{result.get('item_name')}</td>
                <td>{result.get('mrp')}</td>
                <td>{result.get('quantity')}</td>
                <td>{result.get('mrp_total')}</td>
                <td>{result.get('discount')}</td>
                <td>{result.get('total_amount')}</td>
            </tr>
        """

        tr_total_row = f"""
            <tr>
                <td colspan='2'>Total</td>     
                <td>{invoice_item_total.get('total_qty')}</td>     
                <td>{invoice_item_total.get('mrp_total_price')}</td>     
                <td>{invoice_item_total.get('total_discount')}</td>     
                <td>{invoice_item_total.get('total_amount_')}</td>   
            </tr>  
        """

        tr_special_note = f"""
            <tr style="background:#c3e0aad4">
                <td colspan='6'>Note: {result['special_note']}</td>  
            </tr>
        """
        tr_return_head = """
            <tr>
                <td colspan='6' class="font-weight-bold text-center" style="background:#c3e0aad4">Exchange Product List</td>
            </tr>
        """
        tr_return_row = f"""
            <tr>
                <td>{result.get('item_name')}</td>
                <td style="background:#ffff0085">{result.get('mrp')}</td>
                <td style="background:#ffff0085">{result.get('quantity')}</td>
                <td style="background:#ffff0085">{result.get('mrp_total')}</td>
                <td style="background:#ffff0085">{result.get('discount')}</td>
                <td style="background:#ffff0085">{result.get('total_amount')}</td>
            </tr>
        """

        if next_invoice and invoice_name == next_invoice:
            if sales_data.get(invoice_name):
                if result['is_return'] == 1:
                    sales_data[invoice_name].append(tr_return_row)
                else:
                    sales_data[invoice_name].append(tr_rowspan)
            else:
                if result['is_return'] == 1:
                    if sales_data == {}:
                        sales_data[invoice_name] = [tr_return_with_header]
                    elif sales_data.get(result['return_against']):
                        if invoice_item_total['exchange_item'] == result['idx']:
                            sales_data[result['return_against']].append(tr_return_head)
                        sales_data[result['return_against']].append(tr_return_row)
                    else:
                        sales_data[invoice_name] = [tr_return_with_header]
                else:
                    sales_data[invoice_name] = [tr_first_row]

        elif next_invoice and invoice_name != next_invoice:
            if sales_data.get(invoice_name):
                if result['is_return'] == 1:
                    sales_data[invoice_name].append(tr_return_row)
                else:
                    sales_data[invoice_name].append(tr_rowspan)
                if result['is_return'] == 0:
                    sales_data[invoice_name].append(tr_total_row)
                if result['special_note']:
                    sales_data[invoice_name].append(tr_special_note)
            else:
                if result['is_return'] == 1:
                    if sales_data == {}:
                        if invoice_item_total['exchange_item'] == result['idx']:
                            sales_data[invoice_name].append(tr_return_head)
                        sales_data[invoice_name] = [tr_return_with_header]
                        if result['special_note']:
                            sales_data[invoice_name].append(tr_special_note)
                    elif sales_data.get(result['return_against']):
                        if invoice_item_total['exchange_item'] == result['idx']:
                            sales_data[result['return_against']].append(tr_return_head)
                        sales_data[result['return_against']].append(tr_return_row)
                        if result['special_note']:
                            sales_data[result['return_against']].append(tr_special_note)
                    else:
                        sales_data[invoice_name] = [tr_return_with_header]
                    # if result['special_note']:
                    #     sales_data[result['return_against']].append(tr_special_note)
                else:
                    sales_data[invoice_name] = [tr_first_row]
                    sales_data[invoice_name].append(tr_total_row)
                    if result['special_note']:
                        sales_data[invoice_name].append(tr_special_note)

        elif next_invoice == False:
            if sales_data.get(invoice_name):
                if result['is_return'] == 1:
                    sales_data[invoice_name].append(tr_return_row)
                else:
                    sales_data[invoice_name].append(tr_rowspan)
                if result['is_return'] == 0:
                    sales_data[invoice_name].append(tr_total_row)
                if result['special_note']:
                    sales_data[invoice_name].append(tr_special_note)

            else:
                if result['is_return'] == 1:
                    if sales_data == {}:
                        if invoice_item_total['exchange_item'] == result['idx']:
                            sales_data[invoice_name].append(tr_return_head)
                        sales_data[invoice_name] = [tr_return_with_header]
                        if result['special_note']:
                            sales_data[invoice_name].append(tr_special_note)
                    elif sales_data.get(result['return_against']):
                        if invoice_item_total['exchange_item'] == result['idx']:
                            sales_data[result['return_against']].append(tr_return_head)
                        sales_data[result['return_against']].append(tr_return_row)
                        if result['special_note']:
                            sales_data[result['return_against']].append(tr_special_note)
                    else:
                        sales_data[invoice_name] = [tr_return_with_header]
                    # sales_data[result['return_against']].append(tr_special_note)
                else:
                    sales_data[invoice_name] = [tr_first_row]
                    sales_data[invoice_name].append(tr_total_row)
                    if result['special_note']:
                        sales_data[result['return_against']].append(tr_special_note)
        # print('')
        # print('#####################################################')
        # print('')
        # print(invoice_item_total)
        # print('')

    return sales_data
