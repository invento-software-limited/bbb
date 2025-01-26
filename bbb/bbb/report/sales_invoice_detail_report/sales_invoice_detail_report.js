// Copyright (c) 2016, Invento Software Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Invoice Detail Report"] = {
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
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query",
				};
			}
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group"
		},
		{
			"fieldname": "item_brand",
			"label": __("Item Brand"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Brand"
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Customer"
		},
		{
			"fieldname": "served_by",
			"label": __("Served By"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Served By",
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
	]
};
