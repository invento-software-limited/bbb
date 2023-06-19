// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Advance Booking List Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": ["", "To Deliver and Bill", "To Bill", "To Deliver", "Completed"],
			"width": "60px"
		},
		{
			"fieldname": "billing_status",
			"label": __("Billing Status"),
			"fieldtype": "Select",
			"options": ["", "Not Billed", "Fully Billed", "Partly Billed", "Closed"],
			"width": "60px"
		},
		{
			"fieldname": "outlet",
			"label": __("Outlet"),
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": "60px"
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_default('company'),
			// "reqd": 1,
			"width": "60px"
		},
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "status" && data.status === "Completed"){
			value = "<span style='color:green'>" + value + "</span>";
		  }
		else if(column.fieldname == "status"){
			value = "<span style='color:dark'>" + value + "</span>";
		}
		if (column.fieldname == "billing_status" && data && data.billing_status === "Not Billed"){
		  value = "<span style='color:red'>" + value + "</span>";
		}
		else if (column.fieldname == "billing_status" && data && data.billing_status === "Fully Billed"){
			value = "<span style='color:green'>" + value + "</span>";
		  }
		else if (column.fieldname == "billing_status" && data && data.billing_status === "Partly Billed"){
			value = "<span style='color:orange'>" + value + "</span>";
		}
		else if (column.fieldname == "billing_status" && data && data.billing_status === "Closed"){
			value = "<span style='color:dark'>" + value + "</span>";
		}
		return value;
	  },
};
