// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Profit-Loss Summary Report"] = {
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
			"fieldname":"outlet",
			"label": __("Outlet"),
			"fieldtype": "Link",
			"options": "POS Profile",
			"width": "60px",
      "get_query": () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company
					}
				};
			},
      "on_change": function () {
        if(this.value === 'Distribution'){
          frappe.query_report.set_filter_value('switch_invoice', "Sales Invoice");
        }else{
          frappe.query_report.set_filter_value('switch_invoice', "POS Invoice");
        }
      }
		},
    {
      "fieldname": "switch_invoice",
      "label": __("Switch Invoice"),
      "fieldtype": "Data",
      "reqd": 1,
      "read_only": 1,
      "default": "POS Invoice",
    },
    {
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
      "default": frappe.defaults.get_default('company'),
			"reqd": 1,
			"width": "60px",
      "on_change": function (){
        frappe.query_report.set_filter_value('switch_invoice', "POS Invoice")
      }
		},
	]
};
