// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Woocommerce Order Summary Report"] = {
	"filters": [

		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname":"brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item",
			"get_query": function() {
				const item_group = frappe.query_report.get_filter_value('item_group');
				const brand = frappe.query_report.get_filter_value('brand');
				let filters = {}
				if(item_group && brand){
					filters = {'item_group': item_group, 'brand': brand} 
				}else if(item_group){
					filters ={'item_group': item_group} 
				}else if(brand){
					filters = {'brand': brand} 
				}
				return {
					query: "erpnext.controllers.queries.item_query",
					filters: filters
				}
			}
		},
		{
			"fieldname":"status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["Ordered", "Fulfilled", "Cancelled"]
		},
		{
			"fieldname":"periodicity",
			"label": __("Periodicity"),
			"fieldtype": "Select",
			"default": "Daily",
			"options": ["Daily", "Weekly", "Monthly"]
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		}
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "status" && data && data.status == 'Cancelled') {
			value = "<span style='color:red; font-weight:700' class='text text-bold'>" + value + "</span>";
		}
		else if (column.fieldname == "status" && data && data.status == 'Ordered') {
			value = "<span style='color:green' class='text text-bold'>" + value + "</span>";
		}
		else if (column.fieldname == "status" && data && data.status == 'Fulfilled') {
			value = "<span style='color:blue' class='text text-bold'>" + value + "</span>";
		}

		return value;
	},
};
