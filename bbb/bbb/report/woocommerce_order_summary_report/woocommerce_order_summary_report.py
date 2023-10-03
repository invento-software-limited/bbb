# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt
import json
import datetime
from collections import defaultdict

import frappe
from frappe import _

def execute(filters=None):
    currency = filters.presentation_currency or frappe.get_cached_value(
        "Company", filters.company, "default_currency"
    )
    
    data, message, chart, summary_data = get_data(filters, currency)
    columns = get_columns()
    return columns, data, message, chart, summary_data


def get_data(filters, currency):
    conditions = get_conditions(filters)
    query_result = frappe.db.sql(
        """select name, status, posting_date, posting_time, json_data, company from `tabWoocommerce Order` as wc_order where wc_order.docstatus=1 and {} order by wc_order.posting_date asc""".format(conditions), as_dict=True)
    
    # query_result = frappe.db.sql("""select name, status, posting_date, posting_time, json_data, company from `tabWoocommerce Order` where docstatus=1 limit 100""", as_dict=True)

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
            
            total_sell_qty += total_qty
            total_fulfilled_qty += fulfilled_qty
            total_ordered_qty += ordered_qty
            total_cancelled_qty += cancelled_qty
            
            woocommerce_data.append({
                'indent': 0,
                'is_group': 1,
                'posting_date' : str(data.get('posting_date')),
                'qty' : str(total_qty),
                'status' : status,
                'name': data.get('name')
            })
    
    if filters.periodicity == 'Daily':
        woocommerce_data, chart_data = get_daily_report(woocommerce_data)
    elif filters.periodicity == 'Weekly':
        woocommerce_data, chart_data = get_weekly_report(woocommerce_data)
    elif filters.periodicity == 'Monthly':
        woocommerce_data, chart_data = get_monthly_data(woocommerce_data)
     
    # summary data : number cart
    summary_data = [
        {"value": total_ordered_qty, "label": "Ordered Qty", "datatype": "Int", "indicator": "Green"},
        {"value": total_fulfilled_qty, "label": "Fulfilled Qty", "datatype": "Int", "indicator": "Blue"},
        {"value": total_cancelled_qty, "label": "Cancelled Qty", "datatype": "Int", "indicator": "Red",},
        # {"value": total_sell_value, "label": "Total Sell Value", "datatype": "Currency", "currency": currency},
    ]
    
    # chart
    datasets = []
    datasets.append({"name": _("Ordered Qty"), "values": chart_data.get('total_ordered_qty', [])})
    datasets.append({"name": _("Fulfilled Qty"), "values": chart_data.get('total_fulfilled_qty', [])})
    datasets.append({"name": _("Cancelled Qty"), "values": chart_data.get('total_cancelled_qty', [])})
    chart = {"data": {"labels": chart_data.get('labels', []), "datasets": datasets}}
    chart["type"] = "line"
    chart["colors"] = ['#68AB30', '#2490EF', '#dc3545']
    
    message = ''
    
    return woocommerce_data, message, chart, summary_data
 
def get_weekly_report(report_data):
    if len(report_data) < 1:
        return [], {}
    get_data = chunk_list_data(report_data, 6)
    report_data, chart_data = prepare_data(list(get_data), 'Weekly') 
    return report_data, chart_data


def get_daily_report(report_data, sum_qty=False):
    if len(report_data) < 1:
        return [], {}
    tmp = defaultdict(list)
    for item in report_data:
        tmp[item['posting_date']].append(item)
    parsed_list = [v for k,v in tmp.items()]
    report_data, chart_data = prepare_data(parsed_list, 'Daily', sum_qty)
    return report_data, chart_data


def get_monthly_data(report_data):
    if len(report_data) < 1:
        return [], {}
    tmp = defaultdict(list)
    for item in report_data:
        month = datetime.datetime.strptime(item['posting_date'], "%Y-%m-%d").strftime("%B")
        tmp[month].append(item)
    parsed_list = [v for k,v in tmp.items()]
    report_data, chart_data = prepare_data(parsed_list, 'Monthly')
    return report_data, chart_data


def prepare_data(data, periodicity, sum_qty=False):
    report_data = []
    chart_data = {"labels": [], 'total_ordered_qty': [], 'total_fulfilled_qty': [], 'total_cancelled_qty': []}
    for week_data in data:
        start_date = week_data[0]['posting_date']
        ordered_qty, cancelled_qty, fulfilled_qty = 0, 0, 0
        if not sum_qty:
            tmp_list = []
            for single_data in week_data:
                status = single_data.get('status')
                qty = float(single_data['qty'])
                if status == 'Ordered':
                    ordered_qty += qty
                elif status == 'Fulfilled':
                    fulfilled_qty += qty
                elif status == 'Cancelled':
                    cancelled_qty += qty
                    
                if periodicity != "Daily" and not sum_qty:
                    tmp_list.append({
                    'indent': 0,
                    'is_group': 1,
                    'posting_date' : str(single_data.get('posting_date')),
                    'qty' : qty,
                    'status' : status,
                    'name': single_data.get('name')
                })
                    
            tmp_list, ext = get_daily_report(tmp_list, True)
            end_date = single_data['posting_date']
            if periodicity == "Daily":
                date = start_date
            elif periodicity == "Weekly":
                date = '{} - {}'.format(start_date, end_date)
            elif periodicity == "Monthly":
                date = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime("%B")
            else:
                date = ''
            
            report_data.append({
                    'indent': 0,
                    'is_group': 1,
                    'posting_date':  date,
                    'ordered_qty': str(ordered_qty),
                    'cancelled_qty': str(cancelled_qty),
                    'fulfilled_qty': str(fulfilled_qty),
                    
                })
            report_data = report_data + tmp_list

            chart_data["labels"].append(date)
            chart_data["total_ordered_qty"].append(ordered_qty)
            chart_data["total_fulfilled_qty"].append(fulfilled_qty)
            chart_data["total_cancelled_qty"].append(cancelled_qty)
        else:
            tmp_list = []
            for single_data in week_data:
                status = single_data.get('status')
                qty = float(single_data['qty'])
                if status == 'Ordered':
                    ordered_qty += qty
                elif status == 'Fulfilled':
                    fulfilled_qty += qty
                elif status == 'Cancelled':
                    cancelled_qty += qty
                    
            tmp_list.append({
                'indent': 1,
                'is_group': 0,
                'posting_date':  single_data.get('posting_date'),
                'ordered_qty': "val_" + str(ordered_qty),
                'cancelled_qty': "val_" + str(cancelled_qty),
                'fulfilled_qty': "val_" + str(fulfilled_qty),
                
            })
            return tmp_list, []
            
    return report_data, chart_data


def chunk_list_data(list_data, n):
    new_list = []
    for i in range(0, len(list_data), n):
        data = yield list_data[i:i + n]
        new_list.append(data)
    return new_list


def get_columns():
    columns = [
        {"label": _("Date"), "fieldname": "posting_date", "fieldtype": "Text", "width": 200},
        {
            "label": _("Ordered Qty"),
            "fieldname": "ordered_qty",
            "fieldtype": "Text",
            "width": 130,
        },
        {
            "label": _("Fulfilled Qty"),
            "fieldname": "fulfilled_qty",
            "fieldtype": "Text",
            "width": 130,
        },
        {
            "label": _("Cancelled Qty"),
            "fieldname": "cancelled_qty",
            "fieldtype": "Text",
            "width": 130,
        },
    ]

    return columns

def get_conditions(filters):
    conditions = []
        
    if filters.get("from_date"):
        conditions.append("wc_order.posting_date>='%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("wc_order.posting_date<='%s'" % filters.get("to_date"))
    # if filters.get("status"):
    #     conditions.append("wc_order.status = '%s'" % filters.get("status"))
    # if filters.get("company"):
    #     conditions.append("wc_order.company='%s'" % filters.get("company"))
    if conditions:
        conditions = " and ".join(conditions)
    return conditions
