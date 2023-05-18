// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Service Record Report"] = {
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
    }, {
      "fieldname": "status",
      "label": __("Status"),
      "fieldtype": "Select",
      "options": ["", "Pending For Service", "In Progress", "Paused", "Submitted", "Cancelled"],
    },
  ],

  "formatter": function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    if (column.fieldname == "status" && data && data.status === "Pending For Service") {
      value = "<span style='color:orange'>" + value + "</span>";
    } else if (column.fieldname == "status" && data && data.status === "In Progress") {
      value = "<span style='color:green'>" + value + "</span>";
    } else if (column.fieldname == "status" && data && data.status === "Paused") {
      value = "<span style='color:darkgrey'>" + value + "</span>";
    } else if (column.fieldname == "status" && data && data.status === "Submitted") {
      value = "<span style='color:blue'>" + value + "</span>";
    } else if (column.fieldname == "status" && data && data.status === "Cancelled") {
      value = "<span style='color:red'>" + value + "</span>";
    }


    if (column.fieldname == 'view') {
      value = `<div style="background-color: #f5f7fa; cursor: pointer;" class="disabled" onclick="(()=> (frappe.query_reports['Service Record Report']).set_route('` + data.name + `'))()">View</div>`;
    }
    return value;
  },
  "set_route":(value)=>{
    window.open("/app/service-record/"+ value, "_blank")
  }
};
