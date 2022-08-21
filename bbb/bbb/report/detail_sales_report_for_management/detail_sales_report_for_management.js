// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Detail Sales Report For Management"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"outlet",
			"label": __("Outlet"),
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": "60px"
		},
		{
			"fieldname":"switch_invoice",
			"label": __("Switch Invoice"),
			"fieldtype": "Select",
			"options": ["POS Invoice"],
			"default": "POS Invoice",
			"reqd": 1,
			"width": "60px"
		},
	]
};
