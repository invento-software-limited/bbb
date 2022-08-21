# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


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
<table class="table table-bordered" style="margin-top: -15px;">
  <thead>
    <tr>
      <th scope="col" style="font-weight:400" width="55%">Product Name</th>
      <th scope="col" style="font-weight:400" width="10%">Unit Price</th>
      <th scope="col" style="font-weight:400" width="5%">Qty</th>
      <th scope="col" style="font-weight:400" width="10%">MRP</th>
      <th scope="col" style="font-weight:400" width="10%">Disc</th>
      <th scope="col" style="font-weight:400" width="10%">Total</th>
    </tr>
  </thead>
</table>
"""

table_head = """
    <div class="row">
        <div class="col-md-7" style="margin-right:1px solid #ebeef0">Product Name</div>
        <div class="col-md-1">Unit Price</div>
        <div class="col-md-1">Qty</div>
        <div class="col-md-1">MRP</div>
        <div class="col-md-1">Disc</div>
        <div class="col-md-1">Total</div>
    </div>
"""

table_body = """
<table class="table table-bordered" style="margin-top: -15px;">
  <tbody>
    <tr>
      <td scope="col" style="font-weight:300; font-size: 10px;padding:0.5rem !important; white-space: pre-wrap;!important" width="55%">{item_name}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{rate}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="5%">{qty}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{mrp}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{disc}</td>
      <td scope="col" style="font-weight:400;font-size: 12px;" width="10%">{total}</td>
    </tr>
  </tbody>
</table>
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
        conditions.append("sales_invoice.pos_profile = '%s'" % filters.get("pos_profile"))

    if conditions:
        conditions = " and ".join(conditions)
    return conditions


def get_invoice_data(filters):
    conditions = get_conditions(filters)
    invoice_type = filters.get('switch_invoice', "Sales Invoice")
    query_result = frappe.db.sql("""
    		select
    			sales_invoice.pos_profile, sales_invoice.total_taxes_and_charges as vat, sales_invoice.name, sales_invoice.posting_date, sales_invoice.posting_time, 
    			sales_invoice_item.price_list_rate as unit_price, sales_invoice_item.rate as selling_rate, item.standard_rate as mrp,
    			sales_invoice_item.qty as quantity, sales_invoice_item.item_name, item.standard_rate as mrp, sales_invoice.served_by,
    			(sales_invoice_item.qty * item.standard_rate) as mrp_total, ((sales_invoice_item.qty * sales_invoice_item.rate) - (sales_invoice_item.qty * item.buying_rate)) as profit_loss, 
    			(sales_invoice_item.qty * item.buying_rate) as buying_total,
    			((sales_invoice_item.qty * sales_invoice_item.discount_amount)) as discount,
    			(sales_invoice.total - sales_invoice.net_total) as special_discount, sales_invoice.total_qty,
    			 sales_invoice_item.net_amount, sales_invoice_item.amount as total_amount, sales_invoice.customer_name, 
    			 sales_invoice.total, sales_invoice.rounded_total, sales_invoice.total_taxes_and_charges, sales_invoice.net_total, sales_invoice.rounding_adjustment
    		from `tab%s` sales_invoice, `tab%s Item` sales_invoice_item, `tabItem` item
    		where sales_invoice.name = sales_invoice_item.parent and item.item_code = sales_invoice_item.item_code
    			and sales_invoice.docstatus = 1 and %s
    		order by sales_invoice.name
    		""" % (invoice_type, invoice_type, conditions), as_dict=1)

    data = {}
    for result in query_result:
        if data.get(result.get('name')):
            sales_data = data.get(result.get('name'))
            sales_data['mrp_total'] = sales_data['mrp_total'] + result['mrp_total']
            # sales_data['quantity'] = sales_data['quantity'] + result['quantity']
            sales_data['total_selling_rate'] = sales_data['total_selling_rate'] + result['selling_rate']
            sales_data['total_mrp_price'] = sales_data['total_mrp_price'] + result['mrp']
            sales_data['total_amount_'] = sales_data['total_amount_'] + result['total_amount']
            sales_data['total_discount'] = sales_data['total_discount'] + result['discount']
            sales_data['profit_loss'] = sales_data['profit_loss'] + result['profit_loss']
        else:
            result['total_selling_rate'] = result['selling_rate']
            result['total_discount'] = result['discount']
            result['total_amount_'] = result['total_amount']
            result['total_mrp_price'] = result['mrp']
            data[result.get('name')] = result
    sales_data = {}

    for index, result in enumerate(query_result):
        print(result.get('posting_date'))
        next_invoice = True
        invoice_name = result.get('name')
        try:
            next_invoice = query_result[index + 1]
            next_invoice = query_result[index + 1]['name']
        except:
            next_invoice = not next_invoice

        print()
        if next_invoice and invoice_name == next_invoice:
            invoice_dict = {}
            if sales_data.get(invoice_name):
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
                                                                disc=result.get('discount'),
                                                                rate=result.get('selling_rate'),
                                                                qty=result.get('quantity'),
                                                                mrp=result.get('mrp'), total=result.get('total_amount'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)

            else:
                invoice_dict['name'] = invoice_name
                invoice_dict['date'] = result.get('posting_date')
                invoice_dict['time'] = result.get('posting_time')
                invoice_dict['customer'] = result.get('customer_name')
                invoice_dict['pos_profile'] = result.get('pos_profile')
                invoice_dict['served_by'] = result.get('served_by')
                invoice_dict['profit_loss'] = result.get('profit_loss')
                invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
                                                                disc=result.get('discount'),
                                                                rate=result.get('selling_rate'),
                                                                qty=result.get('quantity'),
                                                                mrp=result.get('mrp'), total=result.get('total_amount'))
                invoice_dict['special_discount'] = result.get('special_discount')
                invoice_dict['rounding_adjustment'] = result.get('rounding_adjustment')
                invoice_dict['vat'] = result.get('total_taxes_and_charges')
                invoice_dict['rounded_total'] = result.get('rounded_total')
                sales_data[invoice_name] = [invoice_dict]

        elif next_invoice and invoice_name != next_invoice:
            if sales_data.get(invoice_name):
                invoice_item_total = data.get(invoice_name)
                invoice_dict = {}
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
                                                                disc=result.get('discount'),
                                                                rate=result.get('selling_rate'),
                                                                qty=result.get('quantity'),
                                                                mrp=result.get('mrp'), total=result.get('total_amount'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)

                invoice_dict = {}
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name="Total",
                                                                disc=invoice_item_total.get('total_discount'),
                                                                rate=invoice_item_total.get('total_selling_rate'),
                                                                qty=invoice_item_total.get('total_qty'),
                                                                mrp=invoice_item_total.get('total_mrp_price'),
                                                                total=invoice_item_total.get('total_amount_'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)
            else:
                invoice_item_total = data.get(invoice_name)
                invoice_dict = {}
                invoice_dict['name'] = invoice_name
                invoice_dict['date'] = result.get('posting_date')
                invoice_dict['time'] = result.get('posting_time')
                invoice_dict['customer'] = result.get('customer_name')
                invoice_dict['pos_profile'] = result.get('pos_profile')
                invoice_dict['served_by'] = result.get('served_by')
                invoice_dict['profit_loss'] = result.get('profit_loss')
                invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
                                                                disc=result.get('discount'),
                                                                rate=result.get('selling_rate'),
                                                                qty=result.get('quantity'),
                                                                mrp=result.get('mrp'), total=result.get('total_amount'))
                invoice_dict['special_discount'] = result.get('special_discount')
                invoice_dict['rounding_adjustment'] = result.get('rounding_adjustment')
                invoice_dict['vat'] = result.get('total_taxes_and_charges')
                invoice_dict['rounded_total'] = result.get('rounded_total')
                sales_data[invoice_name] = [invoice_dict]

                invoice_dict = {}
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name="Total",
                                                                disc=invoice_item_total.get('total_discount'),
                                                                rate=invoice_item_total.get('total_selling_rate'),
                                                                qty=invoice_item_total.get('total_qty'),
                                                                mrp=invoice_item_total.get('total_mrp_price'),
                                                                total=invoice_item_total.get('total_amount_'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)

        elif next_invoice == False:
            if sales_data.get(invoice_name):
                invoice_item_total = data.get(invoice_name)
                invoice_dict = {}
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
                                                                disc=result.get('discount'),
                                                                rate=result.get('selling_rate'),
                                                                qty=result.get('quantity'),
                                                                mrp=result.get('mrp'), total=result.get('total_amount'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)

                invoice_dict = {}
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name="Total",
                                                                disc=invoice_item_total.get('total_discount'),
                                                                rate=invoice_item_total.get('total_selling_rate'),
                                                                qty=invoice_item_total.get('total_qty'),
                                                                mrp=invoice_item_total.get('total_mrp_price'),
                                                                total=invoice_item_total.get('total_amount_'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)

            else:
                invoice_item_total = data.get(invoice_name)
                invoice_dict = {}
                invoice_dict['name'] = invoice_name
                invoice_dict['date'] = result.get('posting_date')
                invoice_dict['time'] = result.get('posting_time')
                invoice_dict['customer'] = result.get('customer_name')
                invoice_dict['pos_profile'] = result.get('pos_profile')
                invoice_dict['served_by'] = result.get('served_by')
                invoice_dict['profit_loss'] = result.get('profit_loss')
                invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
                                                                disc=result.get('discount'),
                                                                rate=result.get('selling_rate'),
                                                                qty=result.get('quantity'),
                                                                mrp=result.get('mrp'), total=result.get('total_amount'))
                invoice_dict['special_discount'] = result.get('special_discount')
                invoice_dict['rounding_adjustment'] = result.get('rounding_adjustment')
                invoice_dict['vat'] = result.get('total_taxes_and_charges')
                invoice_dict['rounded_total'] = result.get('rounded_total')
                sales_data[invoice_name] = [invoice_dict]

                invoice_dict = {}
                invoice_dict['name'] = ''
                invoice_dict['date'] = ''
                invoice_dict['time'] = ''
                invoice_dict['customer'] = ''
                invoice_dict['pos_profile'] = ''
                invoice_dict['served_by'] = ''
                invoice_dict['description'] = table_body.format(item_name="Total",
                                                                disc=invoice_item_total.get('total_discount'),
                                                                rate=invoice_item_total.get('total_selling_rate'),
                                                                qty=invoice_item_total.get('total_qty'),
                                                                mrp=invoice_item_total.get('total_mrp_price'),
                                                                total=invoice_item_total.get('total_amount_'))
                invoice_dict['special_discount'] = ''
                invoice_dict['rounding_adjustment'] = ''
                invoice_dict['vat'] = ''
                invoice_dict['rounded_total'] = ''
                sales_data[invoice_name].append(invoice_dict)

        # else:
        #     invoice_item_total = data.get(invoice_name)
        #     invoice_dict = {}
        #     invoice_dict['name'] = ''
        #     invoice_dict['date'] = ''
        #     invoice_dict['time'] = ''
        #     invoice_dict['customer'] = ''
        #     invoice_dict['pos_profile'] = ''
        #     invoice_dict['served_by'] = ''
        #     invoice_dict['description'] = table_body.format(item_name=result.get('item_name'),
        #                                                     disc=result.get('discount'),
        #                                                     rate=result.get('selling_rate'), qty=result.get('quantity'),
        #                                                     mrp=result.get('mrp'), total=result.get('total_amount'))
        #     invoice_dict['special_discount'] = ''
        #     invoice_dict['rounding_adjustment'] = ''
        #     invoice_dict['vat'] = ''
        #     invoice_dict['rounded_total'] = ''
        #     sales_data[invoice_name] = [invoice_dict]
        #
        #     invoice_dict = {}
        #     invoice_dict['name'] = ''
        #     invoice_dict['date'] = ''
        #     invoice_dict['time'] = ''
        #     invoice_dict['customer'] = ''
        #     invoice_dict['pos_profile'] = ''
        #     invoice_dict['served_by'] = ''
        #     invoice_dict['description'] = table_body.format(item_name="Total",
        #                                                     disc=invoice_item_total.get('total_discount'),
        #                                                     rate=invoice_item_total.get('total_selling_rate'),
        #                                                     qty=invoice_item_total.get('total_qty'),
        #                                                     mrp=invoice_item_total.get('total_mrp_price'),
        #                                                     total=invoice_item_total.get('total_amount_'))
        #     invoice_dict['special_discount'] = ''
        #     invoice_dict['rounding_adjustment'] = ''
        #     invoice_dict['vat'] = ''
        #     invoice_dict['rounded_total'] = ''
        #     sales_data[invoice_name].append(invoice_dict)

    invoice_final_data = []
    for invoice_name, invoice_data in sales_data.items():
        invoice_final_data = invoice_final_data + invoice_data

    return invoice_final_data
