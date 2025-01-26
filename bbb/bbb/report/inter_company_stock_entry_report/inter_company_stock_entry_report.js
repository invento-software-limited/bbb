// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Inter Company Stock Entry Report"] = {
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
			"fieldname":"source_company",
			"label": __("Source Company"),
			"fieldtype": "Link",
			"options": "Company",
		},
		{
			"fieldname":"source_warehouse",
			"label": __("Source Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"get_query": () => {
				var company = frappe.query_report.get_filter_value('source_company');
				return {
					filters: {
						'company': company
					}
				};
			}
		},
		{
			"fieldname":"target_company",
			"label": __("Target Company"),
			"fieldtype": "Link",
			"options": "Company",
		},
		{
			"fieldname":"target_warehouse",
			"label": __("Target Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"get_query": () => {
				var company = frappe.query_report.get_filter_value('target_company');
				return {
					filters: {
						'company': company
					}
				};
			}
		},
	]
};
