// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Product Search Log Detail"] = {
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
			"fieldname": "product",
			"label": __("Item"),
			"fieldtype": "Link",
			"width": "200",
			"options": "Item",
		},
		{
			"fieldname": "served_by",
			"label": __("Served By"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Served By"
		},
		{
			"fieldname": "location",
			"label": __("Location"),
			"fieldtype": "Link",
			"width": "80",
			"options": "POS Profile"
		},
		{
			"fieldname": "customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Customer"
		},
		{
			"fieldname": "is_sale",
			"label": __("Sold Item"),
			"fieldtype": "Select",
			"default": "All",
			"options": ["All", "Sold Item", "Unsold Item"]
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Company",
			"default": frappe.defaults.get_default("company")
		},
	],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data !== undefined) {
            if (column.fieldname === "is_sale" && data.is_sale === "Yes") {
                value = "<span style='color:green'>" + value + "</span>";
            }
        }
        return value

    },
};
