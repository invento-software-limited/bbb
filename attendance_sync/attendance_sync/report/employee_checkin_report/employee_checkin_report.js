// Copyright (c) 2016, Invento and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Checkin Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"options": "Today",
			// "get_query": function() {
			// 	return {
			// 		query: "frappe.datetime.datetime.get_today()",
			// 	};
			// }
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "100",
			"options": "Today"
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"width": "10",
			"options": "Employee"
		},
		// {
		// 	"fieldname": "brand",
		// 	"label": __("Brand"),
		// 	"fieldtype": "Link",
		// 	"width": "100",
		// 	"options": "Brand",
			// get_query: () => {
			// 	let warehouse_type = frappe.query_report.get_filter_value("warehouse_type");
			// 	let company = frappe.query_report.get_filter_value("company");

			// 	return {
			// 		filters: {
			// 			...warehouse_type && {warehouse_type},
			// 			...company && {company}
			// 		}
			// 	}
			// }
		// },
		// {
		// 	"fieldname": "company",
		// 	"label": __("Company"),
		// 	"fieldtype": "Link",
		// 	"width": "100",
		// 	"options": "Company",
		// 	"default": frappe.defaults.get_default("company")
		// },
	],
};
