# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt
import json
import math

import frappe
from frappe import _

from erpnext.accounts.report.financial_statements import (
	get_filtered_list_for_consolidated_report,
	get_period_list,
)
from erpnext.accounts.utils import get_account_currency, get_fiscal_years
from frappe.utils import add_days, add_months, cint, cstr, flt, formatdate, get_first_day, getdate

def execute(filters=None):
    from_fiscal_year = get_fiscal_years(filters.from_date, company=filters.company)
    to_fiscal_year = get_fiscal_years(filters.to_date, company=filters.company)

    currency = filters.presentation_currency or frappe.get_cached_value(
        "Company", filters.company, "default_currency"
    )
    
    data, message, chart, summary_data = get_data(filters, currency)
    columns = get_columns()
    return columns, data, message, chart, summary_data


def get_data(filters, currency):
    conditions = get_conditions(filters)
    # if conditions:
    #     query_result = frappe.db.sql(f"""select posting_date, posting_time, json_data from `tabWoocommerce Order` as order where {conditions}""", as_dict=True)
    # else:
    query_result = frappe.db.sql("""select name, status, posting_date, posting_time, json_data, company from `tabWoocommerce Order` limit 100""", as_dict=True)


    total_sell_qty = 0
    total_sell_value = 0
    total_ordered_qty = 0
    total_fulfilled_qty = 0
    total_cancelled_qty = 0
    
    woocommerce_data = []
    chart_data = {}
    current_date = None
    temp_list = []
    indent = 0
    
    if query_result:
        for data in query_result:
            status = data.get('status')
            json_data = data.get('json_data')
            data_dict = json.loads(json_data)
            
            total_qty = sum(product['quantity'] for product in data_dict['line_items'])
            ordered_qty = sum(product['quantity'] if status == "Ordered" else 0 for product in data_dict['line_items'])
            fulfilled_qty = sum(product['quantity'] if status == "Fulfilled" else 0 for product in data_dict['line_items'])
            cancelled_qty = sum(product['quantity'] if status == "Cancelled" else 0 for product in data_dict['line_items'])
            total = sum(float(product['total']) if status != "Cancelled" else 0 for product in data_dict['line_items'])
            subtotal = sum(float(product['subtotal']) if status != "Cancelled" else 0 for product in data_dict['line_items'])
            
            total_sell_qty += total_qty
            total_fulfilled_qty += fulfilled_qty
            total_ordered_qty += ordered_qty
            total_cancelled_qty += cancelled_qty
            total_sell_value += total
            
            
            woocommerce_data.append({
                'indent': 0,
                'is_group': 1,
                'posting_date' : str(data.get('posting_date')),
                # 'woocommerce_id' : str(data_dict.get('id')),
                'total_qty' : str(total_qty),
                # 'voucher_no' : data.get('name'),
                'status' : status,
                'subtotal': str(subtotal),
                'total_amount': str(total),
                'discount_total': str(data.get('discount_total')) if data.get('discount_total') else 0,
            })
            # for wc_item in data_dict['line_items']:
            #     item = frappe.db.get_value('Item', {'woocommerce_id': wc_item.get('product_id')}, ['item_code', 'item_name'])
            #     woocommerce_data.append({
            #     'indent': 1,
            #     'is_group': 0,
            #     'item_name' : '',
            #     'woocommerce_id' : str(wc_item.get('product_id')),
            #     'qty' : str(total_qty),
            #     'voucher_no' : '',
            #     'status' : '',
            #     'company' : data.get('company'),
            # })
    
    if filters.periodicity == 'Daily':
        woocommerce_data, chart_data = get_daily_report(woocommerce_data)
    elif filters.periodicity == 'Weekly':
        woocommerce_data, chart_data = get_weekly_report(woocommerce_data)
    elif filters.periodicity == 'Monthly':
        woocommerce_data, chart_data = get_monthly_data(woocommerce_data)
     
    # summary data : number cart
    summary_data = [
        {"value": total_ordered_qty, "label": "Total Ordered Qty", "datatype": "Int", "indicator": "Green"},
        {"value": total_fulfilled_qty, "label": "Total Fulfilled", "datatype": "Int", "indicator": "Blue"},
        {"value": total_cancelled_qty, "label": "Total Cancelled", "datatype": "Int", "indicator": "Red",},
        {"value": total_sell_value, "label": "Total Sell Value", "datatype": "Currency", "currency": currency},
    ]
    
    # chart
    datasets = []
    datasets.append({"name": _("Total Ordered Qty"), "values": chart_data.get('total_ordered_qty', [])})
    datasets.append({"name": _("Total Fulfilled Qty"), "values": chart_data.get('total_fulfilled_qty', [])})
    datasets.append({"name": _("Total Cancelled Qty"), "values": chart_data.get('total_cancelled_qty', [])})
    chart = {"data": {"labels": chart_data.get('labels', []), "datasets": datasets}}
    chart["type"] = "bar"
    chart["colors"] = ['#68AB30', '#2490EF', '#dc3545']
    
    message = ''
    
    return woocommerce_data, message, chart, summary_data

def get_conditions(filters):

    conditions = []
    if filters.get("from_date"):
        conditions.append("order.posting_date >= '%s'" % filters.get("from_date"))

    if filters.get("to_date"):
        conditions.append("order.posting_date <= '%s'" % filters.get("to_date"))

    if filters.get("status"):
        conditions.append("order.status = '%s'" % filters.get("status"))

    if filters.get("company"):
        conditions.append("order.company = '%s'" % filters.get("company"))
        
        
    if conditions:
        conditions = " and ".join(conditions)

    return conditions

def get_columns():
    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Text", "width": 200},
        # {
        #     "label": _("Voucher"),
        #     "fieldname": "voucher_no",
        #     "fieldtype": "Link",
        #     "options": "Woocommerce Order",
        #     "width": 150,
        # },
        # {
        #     "label": _("Status"),
        #     "fieldname": "status",
        #     "fieldtype": "Text",
        #     "width": 150,
        # },
        # {
        #     "label": _("Woocommerce Id"),
        #     "fieldname": "woocommerce_id",
        #     "fieldtype": "Text",
        #     "width": 100,
        # },
        {
            "label": _("Total Qty"),
            "fieldname": "total_qty",
            "fieldtype": "Text",
            "width": 100,
        },
        {
            "label": _("Sub Total"),
            "fieldname": "subtotal",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Discount Total"),
            "fieldname": "discount_total",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Total"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
    ]

    return columns




# def get_daily_report(report_data):
    

def get_weekly_report(report_data):
    if len(report_data) < 1:
        return []
    get_data = chunk_list_data(report_data, 6)
    week_list = []
    chart_data = {"labels": [], 'total_ordered_qty': [], 'total_fulfilled_qty': [], 'total_cancelled_qty': []}
    for week_data in get_data:
        start_date = week_data[0]['posting_date']
        total_qty = 0
        total = 0
        discount_total = 0
        subtotal = 0
        total_ordered_qty, total_cancelled_qty, total_fulfilled_qty = 0, 0, 0
        for single_data in list(week_data):
            if single_data.get('status') != 'Cancelled':
                total_qty += float(single_data['total_qty'])
                total += float(single_data['total_amount'])
                discount_total += float(single_data['discount_total'])
                subtotal += float(single_data['subtotal'])
                
                if single_data.get('status') == 'Ordered':
                    total_ordered_qty += float(single_data['total_qty'])
                elif single_data.get('status') == 'Fulfilled':
                    total_fulfilled_qty += float(single_data['total_qty']) 
            else:
                total_cancelled_qty += float(single_data['total_qty']) 

        end_date = single_data['posting_date']
        week_list.append({
                'indent': 0,
                'is_group': 1,
                'posting_date':  '{} - {}'.format(start_date, end_date),
                # 'woocommerce_id' : '',
                'total_qty' : str(total_qty),
                # 'voucher_no' : '',
                # 'status' : '',
                'total_amount' : str(total),
                'subtotal': str(subtotal),
                'discount_total': str(discount_total)
            })
        chart_data["labels"].append('{} - {}'.format(start_date, end_date))
        chart_data["total_ordered_qty"].append(total_ordered_qty)
        chart_data["total_fulfilled_qty"].append(total_fulfilled_qty)
        chart_data["total_cancelled_qty"].append(total_cancelled_qty)
        
    return week_list, chart_data

def chunk_list_data(list_data, n):
    new_list = []
    for i in range(0, len(list_data), n):
        data = yield list_data[i:i + n]
        new_list.append(data)
    return new_list


def get_daily_report(report_data):
    from collections import defaultdict 
    if len(report_data) < 1:
        return []
    
    tmp = defaultdict(list)
    for item in report_data:
        tmp[item['posting_date']].append(item)
        
    parsed_list = [{'name':k, 'data':v} for k,v in tmp.items()]
    chart_data = {"labels": [], 'total_ordered_qty': [], 'total_fulfilled_qty': [], 'total_cancelled_qty': []}
    current_date = None
    week_list = []
    
    for week_data in parsed_list:
        start_date = week_data['data'][0]['posting_date']
        total_qty = 0
        total = 0
        discount_total = 0
        subtotal = 0
        total_ordered_qty, total_cancelled_qty, total_fulfilled_qty = 0, 0, 0
        for single_data in week_data['data']:
            if single_data.get('status') != 'Cancelled':
                total_qty += float(single_data['total_qty'])
                total += float(single_data['total_amount'])
                discount_total += float(single_data['discount_total'])
                subtotal += float(single_data['subtotal'])
                
                if single_data.get('status') == 'Ordered':
                    total_ordered_qty += float(single_data['total_qty'])
                elif single_data.get('status') == 'Fulfilled':
                    total_fulfilled_qty += float(single_data['total_qty']) 
            else:
                total_cancelled_qty += float(single_data['total_qty']) 

        end_date = single_data['posting_date']
        week_list.append({
                'indent': 0,
                'is_group': 1,
                'posting_date':  '{}'.format(start_date),
                # 'woocommerce_id' : '',
                'total_qty' : str(total_qty),
                # 'voucher_no' : '',
                # 'status' : '',
                'total_amount' : str(total),
                'subtotal': str(subtotal),
                'discount_total': str(discount_total)
            })
        chart_data["labels"].append('{}'.format(start_date))
        chart_data["total_ordered_qty"].append(total_ordered_qty)
        chart_data["total_fulfilled_qty"].append(total_fulfilled_qty)
        chart_data["total_cancelled_qty"].append(total_cancelled_qty)
        
    return week_list, chart_data


def get_monthly_data(report_data):
    from collections import defaultdict
    import datetime
    
    if len(report_data) < 1:
        return []
    
    tmp = defaultdict(list)
    for item in report_data:
        month = datetime.datetime.strptime(item['posting_date'], "%Y-%m-%d").strftime("%B")
        tmp[month].append(item)
        
    parsed_list = [{'name':k, 'data':v} for k,v in tmp.items()]
    chart_data = {"labels": [], 'total_ordered_qty': [], 'total_fulfilled_qty': [], 'total_cancelled_qty': []}
    current_date = None
    week_list = []
    
    for week_data in parsed_list:
        month = datetime.datetime.strptime(week_data['data'][0]['posting_date'], "%Y-%m-%d").strftime("%B")
        total_qty = 0
        total = 0
        discount_total = 0
        subtotal = 0
        total_ordered_qty, total_cancelled_qty, total_fulfilled_qty = 0, 0, 0
        for single_data in week_data['data']:
            if single_data.get('status') != 'Cancelled':
                total_qty += float(single_data['total_qty'])
                total += float(single_data['total_amount'])
                discount_total += float(single_data['discount_total'])
                subtotal += float(single_data['subtotal'])
                
                if single_data.get('status') == 'Ordered':
                    total_ordered_qty += float(single_data['total_qty'])
                elif single_data.get('status') == 'Fulfilled':
                    total_fulfilled_qty += float(single_data['total_qty']) 
            else:
                total_cancelled_qty += float(single_data['total_qty']) 

        end_date = single_data['posting_date']
        week_list.append({
                'indent': 0,
                'is_group': 1,
                'posting_date':  '{}'.format(month),
                # 'woocommerce_id' : '',
                'total_qty' : str(total_qty),
                # 'voucher_no' : '',
                # 'status' : '',
                'total_amount' : str(total),
                'subtotal': str(subtotal),
                'discount_total': str(discount_total)
            })
        chart_data["labels"].append('{}'.format(month))
        chart_data["total_ordered_qty"].append(total_ordered_qty)
        chart_data["total_fulfilled_qty"].append(total_fulfilled_qty)
        chart_data["total_cancelled_qty"].append(total_cancelled_qty)
        
    return week_list, chart_data