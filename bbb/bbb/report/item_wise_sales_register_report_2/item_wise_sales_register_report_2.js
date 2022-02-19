// Copyright (c) 2016, Invento Bangladesh and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item-wise Sales Register Report 2"] = {
    "filters": [
        {
            "fieldname": "date_range",
            "label": __("Date Range"),
            "fieldtype": "DateRange",
            "default": [frappe.datetime.add_days(frappe.datetime.get_today(), -6), frappe.datetime.add_days(frappe.datetime.get_today(), -3)],
            "reqd": 1
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname": "pos_profile",
            "label": __("Outlet"),
            "fieldtype": "Link",
            "options": "POS Profile",
            "default": frappe.defaults.get_user_default("pos_profile")
        },
        {
            "fieldname": "customer",
            "label": __("Customer"),
            "fieldtype": "Link",
            "options": "Customer"
        },

        // {
        //     "fieldname": "patient_concern",
        //     "label": __("Patient Concern"),
        //     "fieldtype": "Select",
        //     "options": ["", "Regular Skin Care", "Acne Care", "Hair Care", "Pigmentation & Melasma", "Anti-Aging", "Body Shaping and Weight Loss", "Unwanted Hair", "Mole", "Others"]
        // },
        // {
        //     "fieldname": "age",
        //     "label": __("Age: Example age <= 30 "),
        //     "fieldtype": "Int"
        // },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "served_by",
            "label": __("Served By"),
            "fieldtype": "Link",
            "options": "Served By"
        },
        // {
        //     "fieldname": "reference",
        //     "label": __("Reference"),
        //     "fieldtype": "Link",
        //     "options": "Reference"
        // },
        // {
        //     "fieldname": "mode_of_payment",
        //     "label": __("Mode of Payment"),
        //     "fieldtype": "Link",
        //     "options": "Mode of Payment",
        //     "filters": {
        //         "active": 1,
        //     }
        // },
        // {
        //     "fieldname": "sale_type",
        //     "label": __("Sale Type"),
        //     "fieldtype": "Select",
        //     "options": ["", "Instant Sale", "Advance Sale", "Online Sale"]
        // }
    ]
}