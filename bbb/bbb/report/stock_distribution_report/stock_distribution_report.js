// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Distribution Report"] = {
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
			"fieldname": "view",
			"label": __("View"),
			"fieldtype": "Select",
			"width": "80",
			"reqd" : 1,
			"options": ["Summary","Details"],
			"default" : "Summary"
		},
		{
			"fieldname": "stock_distribution",
			"label": __("Stock Distribution"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Stock Distribution",
		},
		{
			"fieldname": "purchase_order",
			"label": __("Purchase Order"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Purchase Order"
		},
		{
			"fieldname": "purchase_receipt",
			"label": __("Purchase Receipt"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Purchase Receipt",
			"depends_on": "eval: doc.view === 'Summary'",
		},
		{
			"fieldname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Supplier"
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
		}
	]
};
