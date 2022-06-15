// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Trust By Activity"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname":"switch_invoice",
			"label": __("Switch Invoice"),
			"fieldtype": "Select",
			"options": ["Sales Invoice", "POS Invoice"],
			"default": "Sales Invoice",
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"purchase_status",
			"label": __("Purchase Status"),
			"fieldtype": "Select",
			"options": ["Has Purchased", "No Purchase"],
			"default": "Has Purchased"
		},
		{
			"fieldname":"only_consultancy",
			"label": __("Only Consultancy"),
			"fieldtype": "Check",
		},
	]
};
