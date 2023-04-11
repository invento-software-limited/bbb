// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Wise Sales Report For Retail Ops"] = {
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
		// {
		// 	"fieldname":"store",
		// 	"label": __("Store"),
		// 	"fieldtype": "Link",
		// 	"options": "Warehouse",
		// 	"width": "60px"
		// },
		{
			"fieldname":"product_code",
			"label": __("Product Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": "60px",
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query"
				}
			}
		},
		{
			"fieldname":"served_by",
			"label": __("Served By"),
            "fieldtype": "Link",
            "width": "80",
            "options": "Served By",
		},
		{
            "fieldname": "item_group",
            "label": __("Item Category"),
            "fieldtype": "Link",
            "width": "80",
            "options": "Item Group",
        },
        {
            "fieldname": "brand",
            "label": __("Brand"),
            "fieldtype": "Link",
            "width": "80",
            "options": "Brand",
        },
		{
			"fieldname":"outlet",
			"label": __("Outlet"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return frappe.db.get_link_options('POS Profile', txt, {
					company: frappe.query_report.get_filter_value("company"),
          profile_type: 'Outlet'
				});
			},
			"width": "60px",
			"default":["Baily Road"],
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
