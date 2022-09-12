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
            "fieldname": "outlet",
            "label": __("Outlet"),
            "fieldtype": "Link",
            "options": "POS Profile",
            "width": "60px"
        },
	]
};
