// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Purchased Customer List"] = {
  "filters": [
    {
      "fieldname": "from_date",
      "label": __("From Date"),
      "fieldtype": "Date",
      "default": frappe.datetime.add_days(frappe.datetime.get_today(), -1),
      "reqd": 1,
    },
    {
      "fieldname": "to_date",
      "label": __("To Date"),
      "fieldtype": "Date",
      "default": frappe.datetime.add_days(frappe.datetime.get_today(), -1),
    },
    {
      "fieldname": "type",
      "label": __(""),
      "fieldtype": "Select",
      "default": "Yesterday",
      "options": ["Yesterday", "Follow-Up 1 Month"],
      "on_change": () => {
        let value = frappe.query_report.get_filter_value('type');
        if (value === "Yesterday") {
          frappe.query_report.set_filter_value('from_date', frappe.datetime.add_days(frappe.datetime.get_today(), -1));
          frappe.query_report.set_filter_value('to_date', frappe.datetime.add_days(frappe.datetime.get_today(), -1));
        } else if (value === "Follow-Up 1 Month") {
          frappe.query_report.set_filter_value('from_date', frappe.datetime.add_months(frappe.datetime.get_today(), -1));
          frappe.query_report.set_filter_value('to_date', frappe.datetime.add_months(frappe.datetime.get_today(), -1));
        }
        frappe.query_report.refresh()
      }
    },
    {
      "fieldname": "pos_profile",
      "label": __("Outlet"),
      "fieldtype": "Link",
      "options": "POS Profile"
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
  "initial_depth": 3,
  "tree": true,
  "parent_field": "voucher_no",
  "name_field": "child",
  "formatter": (value, row, column, data, default_formatter) => {
    value = default_formatter(value, row, column, data);
    if (column.fieldname === "customer_mobile_number") {
      value = `<div class="disabled" style="cursor: copy;" onclick="(()=> frappe.utils.copy_to_clipboard(${value}))()">${value.bold()}</div>`;
    }

    // console.log(frappe)
    if (column.fieldname === "click_here") {
      // value = `<a style='color:green' href='/app/new-customer-feedback' target='_blank' data-doctype='Customer Feedback'>${value.bold()}</a>`;
      if (value === 'feedback_received') {
        value = `<div style="  background-color: #f5f7fa; cursor: pointer; color: green" class="disabled"> ${value ? "Feedback Collected" : ""}</div>`;

      } else {
        value = `<div style="  background-color: #f5f7fa; cursor: pointer;" class="disabled" onclick="(()=> (frappe.query_reports['Purchased Customer List']).make_new_doc('` + value + `'))()"> ${value ? "Create Feedback" : ""}</div>`;

      }
    }
    return value;
  },
  "make_new_doc": (value) => {
    // window.open('/', '_blank')
    // setTimeout(function (){
    //   frappe.new_doc("Customer Feedback", {
    //     'voucher_no': value,
    //     'status' : 'Yesterday Purchased'
    //   },'_blank')
    // }, 1000)
    let report_type = frappe.query_report.get_filter_value('type');
    // if (report_type === 'Follow-Up 1 Month') {
    //   frappe.db.get_list('Customer Feedback', {
    //     fields: ['name'],
    //     filters: {
    //       voucher_no: value
    //     }
    //   }).then(records => {
    //     if (records) {
    //       // frappe.model.set_value('Customer Feedback', records[0]['name'], 'customer_feedback_section', 1)
    //       // frappe.model.set_value('Customer Feedback', records[0]['name'], 'product_feedback_section', 0)
    //       frappe.db.set_value('Customer Feedback', records[0]['name'], 'status', 'Follow-up Customer Feedback')
    //         .then(r => {
    //           let doc = r.message;
    //           var url = frappe.urllib.get_full_url('/desk/customer-feedback/' + doc.name);
    //           window.open(url, '_blank')
    //         })
    //     }
    //
    //   })
    // } else {
      frappe.db.insert({
        doctype: 'Customer Feedback',
        voucher_no: value,
        status: 'Purchased Customer Feedback',
      }).then(doc => {
        var url = frappe.urllib.get_full_url('/desk/customer-feedback/' + doc.name);
        window.open(url, '_blank')
      })
    // }
    // frappe.route_options = {
    //     'voucher_no': value,
    //     'status' : 'Yesterday Purchased'
    //   };
    // frappe.set_route('Form', 'Customer Feedback', 'new','_blank');
    // window.open('/app/customer-feedback/new-customer-feedback', '_blank')
  },
};
