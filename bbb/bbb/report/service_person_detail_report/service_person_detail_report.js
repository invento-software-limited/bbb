// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Service Person Detail Report"] = {
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
      "width": "60px"
    },
    {
      "fieldname": "service_person",
      "label": __("Service Person"),
      "fieldtype": "Link",
      "options": "Service Person",
      "width": "60px"
    },

    {
      "fieldname": "service_name",
      "label": __("Service Name"),
      "fieldtype": "Link",
      "options": "Item",
      "get_query": () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
          filters: [
            {"company" : ["in", [company, null]]}
          ]
				}
			},
      "width": "60px"
    },
    {
      "fieldname": "outlet",
      "label": __("Outlet"),
      "fieldtype": "Link",
      "options": "POS Profile",
      "width": "60px",
      "get_query": () => {
				var company = frappe.query_report.get_filter_value('company');
				return {
          filters: [
            {"company" : ["in", [company]]}
          ]
				}
			},
    },
    {
      "fieldname": "status",
      "label": __("Status"),
      "fieldtype": "Select",
      "options": ["", "Pending For Service", "In Progress", "Paused", "Submitted", "Cancelled"],
      "default": "Submitted",
    },
    {
      "fieldname": "company",
      "label": __("Company"),
      "fieldtype": "Link",
      "options": "Company",
      "default": "Orkas Glam Bar And Revive Spa",
      "width": "60px",
      "read_only":1,
    },
  ],
  "formatter": function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    // let time = frappe.format('3700', {'fieldtype': 'Duration'})
    // if (column.fieldname == "status" && data && data.status === "Pending For Service") {
    //   value = "<span style='color:orange'>" + value + "</span>";
    // } else if (column.fieldname == "status" && data && data.status === "In Progress") {
    //   value = "<span style='color:green'>" + value + "</span>";
    // } else if (column.fieldname == "status" && data && data.status === "Paused") {
    //   value = "<span style='color:darkgrey'>" + value + "</span>";
    // } else if (column.fieldname == "status" && data && data.status === "Submitted") {
    //   value = "<span style='color:blue'>" + value + "</span>";
    // } else if (column.fieldname == "status" && data && data.status === "Cancelled") {
    //   value = "<span style='color:red'>" + value + "</span>";
    // }

    //
    // if (column.fieldname == 'view') {
    //   value = `<div style="background-color: #f5f7fa; cursor: pointer;" class="disabled" onclick="(()=> (frappe.query_reports['Service Record Report']).set_route('` + data.name + `'))()">View</div>`;
    // }
    return value;
  },
};
