// Copyright (c) 2016, Invento Bangladesh and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Analysis"] = {
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
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "100",
			"options": "Item Group",
		},
		// {
		// 	"fieldname": "pos_profile",
		// 	"label": __("Outlet"),
		// 	"fieldtype": "Link",
		// 	"width": "100",
		// 	"options": "POS Profile",
		// },
		// {
		// 	"fieldname": "order_by",
		// 	"label": __("Filter By"),
		// 	"fieldtype": "Select",
		// 	"width": "100",
		// 	"options": ["Quantity", "Amount"],
		// 	"default": "Quantity"
		// },
		// {
		// 	"fieldname": "sort_by",
		// 	"label": __("Sort By"),
		// 	"fieldtype": "Select",
		// 	"width": "100",
		// 	"options": ["Ascending", "Descending"],
		// 	"default": "Descending"
		// },
		{
			"fieldname": "items_quantity",
			"label": __("Items on Chart"),
			"fieldtype": "Select",
			"width": "100",
			"options": [10, 20, 50, 100, 200, 500, 1000, "All"],
			"default": 20
		},
    {
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
      "default": frappe.defaults.get_default('company'),
			// "reqd": 1,
			"width": "60px"
		},
	]
};
