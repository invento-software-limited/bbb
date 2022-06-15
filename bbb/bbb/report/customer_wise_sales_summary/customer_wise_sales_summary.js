// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Wise Sales Summary"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
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
			"fieldname":"pos_profile",
			"label": __("Outlet"),
			"fieldtype": "Link",
			"options": "POS Profile",
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
		},
	]
};
