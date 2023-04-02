// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Trust By Activity"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start(),
			"reqd": 1,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
		},
		{
			"fieldname":"purchase_status",
			"label": __("Purchase Status"),
			"fieldtype": "Select",
			"options": ["Has Purchased", "No Purchase"],
			"default": "Has Purchased"
		},
		{
			"fieldname":"customer_group",
			"label": __("Customer Group"),
			"fieldtype": "Link",
			"options": "Customer Group",
      "default": 'Basic'

		},
		{
			"fieldname":"only_consultancy",
			"label": __("Only Consultancy"),
			"fieldtype": "Check",
		},
		{
			"fieldname":"sales_type",
			"label": __("Sales Type"),
			"fieldtype": "Select",
			"options": ["Outlet", "Distribution", "Online"],
      "default": "Outlet",
      "on_change": function () {
        if(this.value === 'Distribution'){
          frappe.query_report.set_filter_value('customer_group', "Distribution");
          frappe.query_report.refresh();
        }else if (this.value === 'Outlet'){
          frappe.query_report.set_filter_value('customer_group', "Basic");
          frappe.query_report.refresh();
        }else {
          frappe.query_report.set_filter_value('customer_group', "");
          frappe.query_report.refresh();
        }

      }
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
