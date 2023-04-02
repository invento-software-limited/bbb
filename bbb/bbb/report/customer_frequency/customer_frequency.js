// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Frequency"] = {
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
			"fieldname":"customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group"
		},
		{
			"fieldname":"min_basket_value",
			"label": __("Min. Basket Value"),
			"fieldtype": "Currency",
		},
		{
			"fieldname":"max_basket_value",
			"label": __("Max. Basket value"),
			"fieldtype": "Currency",
		},
		{
			"fieldname":"sales_type",
			"label": __("Sales Type"),
			"fieldtype": "Select",
			"options": ["Outlet", "Distribution", "Online"],
      "default": "Outlet"
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
