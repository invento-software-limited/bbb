// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Customer Birthday List"] = {
  "filters": [
    {
      "fieldname": "customer",
      "label": __("Customer"),
      "fieldtype": "Link",
      "options": "Customer"
    },
    // {
    //   "fieldname": "month",
    //   "label": __("Month"),
    //   "fieldtype": "Select",
    //   "options": "Jan\nFeb\nMar\nApr\nMay\nJun\nJul\nAug\nSep\nOct\nNov\nDec",
    //   "default": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
    //     "Dec"][frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth()],
    //   "on_change": function () {
    //     frappe.query_report.set_filter_value('type', "");
    //     frappe.query_report.refresh();
    //   }
    // },
    {
      "fieldname": "type",
      "label": __(""),
      "fieldtype": "Select",
      "default": "Today",
      "options": ["Today", "Next 7 Days", "Next 30 Days"],
      // "on_change": function () {
      //   frappe.query_report.set_filter_value('month', ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov",
      //   "Dec"][frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth()])
      //   frappe.query_report.refresh();
      // }
    },
    {
      "fieldname": "customer_group",
      "label": __("Customer Group"),
      "fieldtype": "Link",
      "options": "Customer Group"
    },
    {
      "fieldname": "company",
      "label": __("Company"),
      "fieldtype": "Link",
      "options": "Company",
      "width": "60px"
    },
  ],
  formatter: (value, row, column, data, default_formatter) => {
    value = default_formatter(value, row, column, data);
    if (column.fieldname === "mobile_number") {
      value = `<div class="disabled" style="cursor: copy;" onclick="(()=> frappe.utils.copy_to_clipboard(${value}))()">${value}</div>`;
    }
    return value;
  },
}
