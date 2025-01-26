# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(), get_service_data(filters)
    # time = frappe.format('3700', {'fieldtype': 'Duration'})
    return columns, data


def get_columns():
    """return columns"""
    columns = [
        {"label": _("Service Person"), "fieldname": "service_person", "fieldtype": "Text", "width": 120},
        {"label": _("Total Service"), "fieldname": "total_service", "fieldtype": "Int", "width": 120},
        {"label": _("Total Value"), "fieldname": "total_value", "fieldtype": "Text", "width": 100},
        {"label": _("Service Date"), "fieldname": "service_date", "fieldtype": "Text", "width": 120},
        {"label": _("As Person 1"), "fieldname": "service_person_1", "fieldtype": "Text", "width": 150},
        {"label": _("As Person 2"), "fieldname": "service_person_2", "fieldtype": "Text", "width": 150},
        {"label": _("As Person 3"), "fieldname": "service_person_3", "fieldtype": "Text", "width": 150},
        {"label": _("As Person 4"), "fieldname": "service_person_4", "fieldtype": "Text", "width": 150}
    ]
    return columns


def get_conditions(filters):
    conditions = []
    if filters.get("from_date"):
        conditions.append("service_record.service_date >= '%s'" % filters.get("from_date"))
    if filters.get("to_date"):
        conditions.append("service_record.service_date <= '%s'" % filters.get("to_date"))
    if filters.get("service_name"):
        conditions.append("service_record.service_code = '%s'" % filters.get("service_name"))
    if filters.get("location"):
        conditions.append("service_record.location = '%s'" % filters.get("location"))
    if filters.get("status"):
        conditions.append("service_record.status = '%s'" % filters.get("status"))
    if filters.get("company"):
        conditions.append("service_record.company = '%s'" % filters.get("company"))

    if conditions:
        conditions = " and ".join(conditions)

    return conditions


def get_service_person_conditions(filters):
    conditions = []

    if filters.get("service_person"):
        conditions.append("service_record.service_person_1 = '%s'" % filters.get("service_person"))
    if filters.get("service_person"):
        conditions.append("service_record.service_person_2 = '%s'" % filters.get("service_person"))
    if filters.get("service_person"):
        conditions.append("service_record.service_person_3 = '%s'" % filters.get("service_person"))
    if filters.get("service_person"):
        conditions.append("service_record.service_person_4 = '%s'" % filters.get("service_person"))

    if conditions:
        conditions = " or ".join(conditions)

    return conditions


def get_service_data(filters):
    conditions = get_conditions(filters)
    service_person_conditions = get_service_person_conditions(filters)
    if filters.get('service_person'):
        query_result = frappe.db.sql("""
        SELECT name,
        service_name,
        service_code,
        invoice_no,
        location,
        service_person_1,
        service_person_2,
        service_person_3,
        service_person_4,
        service_person_1_weight,
        service_person_2_weight,
        service_person_3_weight,
        service_person_4_weight,
        total_service_time,
        status,
        company
        FROM `tabService Record` service_record
        WHERE %s and (%s)""" % (conditions, service_person_conditions), as_dict=1)
    else:
        query_result = frappe.db.sql("""
        SELECT service_record.name,
        service_record.service_date,
        service_record.service_name,
        service_record.service_code,
        service_record.invoice_no,
        service_record.location,
        service_record.service_person_1,
        service_record.service_person_2,
        service_record.service_person_3,
        service_record.service_person_4,
        service_record.service_person_1_weight,
        service_record.service_person_2_weight,
        service_record.service_person_3_weight,
        service_record.service_person_4_weight,
        service_record.total_service_time,
        service_record.status,
        service_record.company,
        item.discount_amount,
        item.net_amount,
        item.amount
        FROM `tabService Record` service_record JOIN `tabPOS Invoice Item` item ON item.parent=service_record.invoice_no
        WHERE item.item_code=service_record.service_code and %s""" % (conditions), as_dict=1)

    service_person_list = []
    index_increment = 0
    final_data = []
    for result in query_result:
        if result.get('service_person_1', None):
            service_person_1_weight = result.get('service_person_1_weight', 1)
            value = get_value(service_person_1_weight, result.get('net_amount'))
            service_person = result.get('service_person_1')
            if service_person in service_person_list:
                index_increment = index_increment + 1
                index = service_person_list.index(service_person)
                final_data[index]['total_service'] = final_data[index]['total_service']  + 1
                final_data[index]['total_value'] = final_data[index]['total_value']  + value
                temp = get_service_person_dict(False, "1", result, value)
                final_data.insert(index + index_increment, temp)
            else:
                service_person_list.append(service_person)
                temp = get_service_person_dict(True, "1", result, value)
                index_increment = 0
                final_data.append(temp)

        if result.get('service_person_2', None):
            service_person_2_weight = result.get('service_person_2_weight', 1)
            value = get_value(service_person_2_weight, result.get('net_amount'))
            service_person = result.get('service_person_2')
            if service_person in service_person_list:
                index_increment = index_increment + 1
                index = service_person_list.index(service_person)
                final_data[index]['total_service'] = final_data[index]['total_service']  + 1
                final_data[index]['total_value'] = final_data[index]['total_value']  + value
                temp = get_service_person_dict(False, "2", result, value)
                final_data.insert(index + index_increment, temp)
            else:
                service_person_list.append(service_person)
                temp = get_service_person_dict(True, "2", result, value)
                index_increment = 0
                final_data.append(temp)
        if result.get('service_person_3', None):
            service_person_3_weight = result.get('service_person_3_weight', 1)
            value = get_value(service_person_3_weight, result.get('net_amount'))
            service_person = result.get('service_person_3')
            if service_person in service_person_list:
                index_increment = index_increment + 1
                index = service_person_list.index(service_person)
                final_data[index]['total_service'] = final_data[index]['total_service']  + 1
                final_data[index]['total_value'] = final_data[index]['total_value']  + value
                temp = get_service_person_dict(False, "1", result, value)
                final_data.insert(index + index_increment, temp)
            else:
                service_person_list.append(service_person)
                temp = get_service_person_dict(True, "1", result, value)
                index_increment = 0
                final_data.append(temp)
        if result.get('service_person_4', None):
            service_person_4_weight = result.get('service_person_4_weight', 1)
            value = get_value(service_person_4_weight, result.get('net_amount'))
            service_person = result.get('service_person_4')
            if service_person in service_person_list:
                index_increment = index_increment + 1
                index = service_person_list.index(service_person)
                final_data[index]['total_service'] = final_data[index]['total_service']  + 1
                final_data[index]['total_value'] = final_data[index]['total_value']  + value
                temp = get_service_person_dict(False, "1", result, value)
                final_data.insert(index + index_increment, temp)
            else:
                service_person_list.append(service_person)
                temp = get_service_person_dict(True, "1", result, value)
                index_increment = 0
                final_data.append(temp)
        # break

    print(final_data)

    return final_data


def get_value(service_person_1_weight, net_amount):
    try:
        value = (float(service_person_1_weight) * float(net_amount)) / 100
        return value
    except:
        return 0

def get_service_person_dict(new_dict=True, service_person='1', result={}, value=0):
    if new_dict:
        temp = {}
        temp['service_person'] = service_person
        temp['total_service'] = 1
        temp['total_value'] = value
        temp['service_date'] = result.get('service_date')
        temp['service_name'] = result['service_name']
        temp['service_person_' + service_person] = value
        return temp
    else:

        temp = {}
        temp['service_person'] = ''
        temp['total_service'] = 1
        temp['total_value'] = ''
        temp['service_date'] = result.get('service_date')
        temp['service_name'] = result['service_name']
        temp['service_person_' + service_person] = value
        return temp
