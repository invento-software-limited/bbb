# Copyright (c) 2013, Invento and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_items(filters)
	return columns, data


def get_items(filters=None):
	conditions = get_conditions(filters)

	query_str = """select employee_checkin.name, employee_checkin.log_type, 
					employee_checkin.time, employee_checkin.employee, employee_checkin.employee_name,
	 				employee.attendance_device_id as attendance_device_id
					from `tabEmployee Checkin` employee_checkin inner join `tabEmployee` employee on employee.name=employee_checkin.employee"""

	if conditions:
		query_str += """ where {}""".format(conditions)
		return frappe.db.sql(query_str, as_dict=True)
	else:
		return frappe.db.sql(query_str, as_dict=True)


def get_columns():
	""" Columns of Report Table"""

	columns = [
		{"label": _("Checkin ID"), "fieldname": "name", "fieldtype": "Data", "width": 250},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 350},
		{"label": _("Attendance Device ID"), "fieldname": "attendance_device_id", "width": 200},
		{"label": _("Log Type"), "fieldname": "log_type", "width": 200},
		{"label": _("Date Time"), "fieldname": "time", "width": 200},
	]

	return columns


def get_conditions(filters=None):
	conditions = []
	from_date = filters.get('from_date')
	to_date = filters.get('to_date')
	employee = filters.get('employee')

	print("=======>>", employee)

	if from_date:
		conditions.append("employee_checkin.time >= '%s'" % from_date)

	if to_date:
		conditions.append("employee_checkin.time <= '%s'" % to_date)

	if employee:
		conditions.append("employee_checkin.employee = '%s'" % employee)

	if conditions:
		conditions = " and ".join(conditions)

	return conditions
