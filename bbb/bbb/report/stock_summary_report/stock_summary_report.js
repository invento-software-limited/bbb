// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Stock Summary Report"] = {
    "filters": [
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
