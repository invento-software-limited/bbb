// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Served By Summary Report"] = {
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
		},{
			"fieldname":"sales_type",
			"label": __("Sales Type"),
			"fieldtype": "Select",
			"options": ["Outlet", "Distribution", "Online"],
      "default": "Outlet",
      "on_change": function (){
          const sales_type = this.value;
          if(sales_type === "Distribution") {
            frappe.query_report.set_filter_value('switch_invoice', "Sales Invoice");
            frappe.query_report.set_filter_value('outlet', []);
            frappe.query_report.set_filter_value('all_outlet', 0);
            frappe.query_report.refresh();
          }else{
            frappe.query_report.set_filter_value('switch_invoice', "POS Invoice");
            frappe.query_report.set_filter_value('outlet', []);
            frappe.query_report.refresh();
          }
      }
		},
		{
			"fieldname":"outlet",
			"label": __("Outlet"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return frappe.db.get_link_options('POS Profile', txt, {
					company: frappe.query_report.get_filter_value("company"),
          profile_type: frappe.query_report.get_filter_value('sales_type')
				});
			},
			"width": "60px",
			"default":["Baily Road"],
      "mandatory_depends_on": frappe.query_report.get_filter_value('all_outlet') === [],
		},
		{
			"fieldname":"all_outlet",
			"label": __("All Outlet"),
			"fieldtype": "Check",
			"default": 0,
			"width": "60px",
      "on_change": function (){
        frappe.query_report.set_filter_value('switch_invoice', "POS Invoice");
        frappe.query_report.set_filter_value('outlet', []);
        frappe.query_report.set_filter_value('sales_type', 'Outlet');
        frappe.query_report.refresh();
      }
		},
		{
			"fieldname":"switch_invoice",
			"label": __("Switch Invoice"),
			"fieldtype": "Data",
			"default": "POS Invoice",
			"reqd": 1,
      "read_only":1,
			"width": "60px"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_default("Company"),
			"reqd": 1,
			"width": "60px",
      "on_change": function (){
        frappe.query_report.set_filter_value('outlet', "");
        frappe.query_report.refresh();
      }
		},
	]
};
