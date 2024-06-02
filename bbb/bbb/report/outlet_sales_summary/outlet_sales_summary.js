// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Outlet Sales Summary"] = {
	"filters": [
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "width": "60px"
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "width": "60px"
        },
		{
			"fieldname":"outlet",
			"label": __("Outlet"),
			"fieldtype": "Link",
			"options": "POS Profile",
      "reqd": 1,
      "get_query": () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
					filters: {
						'company': company,
            'profile_type': 'Outlet'
					}
				};
			},
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
        "default": frappe.defaults.get_default('company'),
        "reqd": 1,
        "width": "60px"
      },
	]
};
