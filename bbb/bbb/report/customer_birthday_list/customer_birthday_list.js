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
    {
      "fieldname": "type",
      "label": __(""),
      "fieldtype": "Select",
      "default": "Today",
      "options": ["Today", "Next 7 Days", "Next 30 Days"]
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
      "default": frappe.defaults.get_default('company'),
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
