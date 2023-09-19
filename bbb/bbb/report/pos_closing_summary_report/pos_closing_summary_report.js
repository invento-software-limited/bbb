// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["POS Closing Summary Report"] = {
    "filters": [
        {
            "fieldname": "date",
            "label": __("Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1,
            "width": "60px"
        },
        {
            "fieldname": "pos_profile",
            "label": __("POS Profile"),
            "fieldtype": "Link",
            "options": "POS Profile",
            "width": "60px",
            "get_query": () => {
                var company = frappe.query_report.get_filter_value('company');
                if (company) {
                    return {
                        filters: {
                            'company': company
                        }
                    };
                }

            },
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": ["", "Open", "Closed"],
            "width": "60px"
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            // "default": frappe.defaults.get_default('company'),
            // "reqd": 1,
            "width": "60px",
            "on_change": function () {
                frappe.query_report.set_filter_value('pos_profile', "");
                frappe.query_report.refresh();
            }
        },
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (data !== undefined) {
            if (column.fieldname === "status" && data.status === "Open") {
                value = "<span style='color:green'>" + value + "</span>";
            } else if (column.fieldname === "status" && data.status === "Closed") {
                value = "<span style='color:#2490EF'>" + value + "</span>";
            } else if (column.fieldname === "status" && data.status !== "Open" && data.status !== "Closed") {
                value = "<span style='color:darkred'>" + value + "</span>";
            }
        }
        return value

    },
};
