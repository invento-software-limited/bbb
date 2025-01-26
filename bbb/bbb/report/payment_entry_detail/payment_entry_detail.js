// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Payment Entry Detail"] = {
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
            "fieldname": "payment_type",
            "label": __("Payment Type"),
            "fieldtype": "Select",
            "options": ['Receive', 'Pay', 'Internal Transfer'],
            "width": "60px"
        },
		{
            "fieldname": "party_type",
            "label": __("Party Type"),
            "fieldtype": "Select",
            "options": ["Customer", "Supplier"],
            "width": "60px"
        },

		{
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer",
            "width": "60px",
            "depends_on": "eval:doc.party_type ==='Customer'",
            "mandatory_depends_on": "eval:doc.party_type ==='Customer'",
        },
		{
            "fieldname": "supplier",
            "label": __("Supplier"),
            "fieldtype": "Link",
            "options": "Supplier",
            "width": "60px",
            "depends_on": "eval:doc.party_type ==='Supplier'",
            "mandatory_depends_on": "eval:doc.party_type ==='Supplier'",


        },
	]
};
