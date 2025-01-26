// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["All Product Info"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
      // "default": frappe.defaults.get_default('company'),
			// "reqd": 1,
			"width": "60px"
		},
  ]
};
