// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Summary Report"] = {
    "filters": [
        {
              "fieldname":"from_date",
              "label": __("Date"),
              "fieldtype": "Date",
              "width": "80",
              "reqd": 1,
              "default": frappe.datetime.get_today(),
              // "default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
        },
        // {
        //       "fieldname":"to_date",
        //       "label": __("To Date"),
        //       "fieldtype": "Date",
        //       "width": "80",
        //       "reqd": 1,
        //       "default": frappe.datetime.get_today()
        // },
        {
            "fieldname": "group_by",
            "label": __("Group By"),
            "fieldtype": "Select",
            "width": "80",
            "reqd": 1,
            "options": ["All", "Item Category", "Brand"],
            "default": "All",
        },
        {
            "fieldname": "item_group",
            "label": __("Item Category"),
            "fieldtype": "Link",
            "width": "80",
            "options": "Item Group",
            "depends_on": "eval: doc.group_by == 'Item Category'",
        },
        {
            "fieldname": "brand",
            "label": __("Brand"),
            "fieldtype": "Link",
            "width": "80",
            "options": "Brand",
            "depends_on": "eval: doc.group_by == 'Brand'",
        },		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "MultiSelectList",
			"get_data" : function(txt) {
				return frappe.db.get_link_options('Warehouse', txt);
			},
			"width": "60px"
		},
		{
			"fieldname":"all_warehouse",
			"label": __("All Warehouse"),
			"fieldtype": "Check",
			"default": 0,
			"width": "60px"
		},
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "width": "80",
            "options": "Company",
            "reqd": 1,
            "default": frappe.defaults.get_user_default("Company"),
            // "depends_on": "eval: doc.group_by != 'Company'",
        },
    ]
};
