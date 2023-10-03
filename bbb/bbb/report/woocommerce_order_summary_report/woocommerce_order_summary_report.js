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
		// {
		// 	"fieldname":"status",
		// 	"label": __("Status"),
		// 	"fieldtype": "Select",
		// 	"options": ["","Ordered", "Fulfilled", "Cancelled"]
		// },
		{
			"fieldname":"periodicity",
			"label": __("Periodicity"),
			"fieldtype": "Select",
			"default": "Daily",
			"options": ["Daily", "Weekly", "Monthly"]
		},

		// {
		// 	"fieldname":"month",
		// 	"label": __("Month"),
		// 	"fieldtype": "MultiSelectList",
		// 	"options": [
		// 		{value:'January', description: ''},
		// 		{value:'February', description: ''},
		// 		{value:'March', description: ''},
		// 		{value:'April', description: ''},
		// 		{value:'May', description: ''},
		// 		{value:'June', description: ''},
		// 		{value:'July', description: ''},
		// 		{value:'August', description: ''},
		// 		{value:'September', description: ''},
		// 		{value:'October', description: ''},
		// 		{value:'November', description: ''},
		// 		{value:'December', description: ''},
		// 	]
		// },
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
		
		if (column.fieldname == "cancelled_qty" && data) {
			if(value.split("_")[0] !== 'val'){
				value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
			}else{
				value = "<span'>" + value.split("_")[1] + "</span>";
			}
		}
		else if (column.fieldname == "ordered_qty" && data) {
			if(value.split("_")[0] !== 'val'){
				value = "<span style='color:green; font-weight:bold'>" + value + "</span>";
			}else{
				value = "<span'>" + value.split("_")[1] + "</span>";
			}
		}
		else if (column.fieldname == "fulfilled_qty" && data) {
			if(value.split("_")[0] !== 'val'){
				value = "<span style='color:blue; font-weight:bold'>" + value + "</span>";
			}else{
				value = "<span'>" + value.split("_")[1] + "</span>";
			}
		}

		return value;
	},
};
