// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt


frappe.ui.form.on('Customer Feedback', {
  // refresh: function(frm) {

  // }
  onload: (frm) => {
    console.log(frm.doc.status)
    // const frm = this
    let item_array = frm.doc.items
    if (item_array === undefined || item_array.length == 0){
      frappe.db.get_doc('POS Invoice', frm.doc.voucher_no)
        .then(doc => {
          $.each(doc.items, function (i, d) {
            let new_item = {'item_code': d.item_code, 'qty': d.qty, 'item_name': d.item_name, 'brand': d.brand}
            console.log(new_item)
            frm.add_child('items', new_item);
          });
          frm.refresh_field('items');
        })
    }
    if (frm.doc.status === 'Purchased Customer Feedback' || frm.doc.status === 'Customer Feedback Collected') {
      frm.set_df_property('customer_feedback_section', 'hidden', 0);
      frm.set_df_property('product_feedback_section', 'hidden', 1);
      frm.refresh_fields();
    } else if (frm.doc.status === 'Customer Feedback Collected') {
      frm.set_df_property('how_helpful_service_team', 'set_only_once', 1);
      frm.set_df_property('how_easy_to_find', 'set_only_once', 1);
      frm.set_df_property('service_comments', 'set_only_once', 1);
      frm.set_df_property('overall_customer_feedback_rating', 'set_only_once', 1);
      frm.refresh_fields();

    } else if (frm.doc.status === 'Follow-up Customer Feedback') {
      frm.set_df_property('customer_feedback_section', 'hidden', 1);
      frm.set_df_property('product_feedback_section', 'hidden', 0);
      frm.refresh_fields();
    } else {
      frm.set_df_property('how_helpful_service_team', 'set_only_once', 1);
      frm.set_df_property('how_easy_to_find', 'set_only_once', 1);
      frm.set_df_property('service_comments', 'set_only_once', 1);
      frm.set_df_property('overall_customer_feedback_rating', 'set_only_once', 1);


      frm.set_df_property('product_quality', 'set_only_once', 1);
      frm.set_df_property('recommended_product', 'set_only_once', 1);
      frm.set_df_property('product_comments', 'set_only_once', 1);
      frm.set_df_property('overall_product_feedback_rating', 'set_only_once', 1);

      frm.set_df_property('customer_feedback_section', 'hidden', 0);
      frm.set_df_property('product_feedback_section', 'hidden', 0);

		  frm.refresh_fields();
    }
  },

  voucher_no: (frm) => {
    // const frm = this
    frappe.db.get_doc('POS Invoice', frm.doc.voucher_no)
      .then(doc => {
        $.each(doc.items, function (i, d) {
          let new_item = {'item_code': d.item_code, 'qty': d.qty, 'item_name': d.item_name, 'brand': d.brand}
          frm.add_child('items', new_item);
        });
        frm.refresh_field('items');
      })
  },
  after_save: (frm) => {
    if (frm.doc.status === 'Purchased Customer Feedback') {
      frappe.db.set_value('Customer Feedback', frm.doc.name, 'status', 'Customer Feedback Collected')
      frm.refresh_fields();
    } else if (frm.doc.status === 'Follow-up Customer Feedback') {
      frappe.db.set_value('Customer Feedback', frm.doc.name, 'status', 'Completed')
      frm.refresh_fields();

    }
  }
});


frappe.ui.form.on('Customer Feedback Item', {
  very_satisfied: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.very_satisfied === 1) {
      frappe.model.set_value(cdt, cdn, 'satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'natural', 0)
      frappe.model.set_value(cdt, cdn, 'dissatisfied', 0)
      frappe.model.set_value(cdt, cdn, 'very_dissatisfied', 0)
    }
  },
  satisfied: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.satisfied === 1) {
      frappe.model.set_value(cdt, cdn, 'very_satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'natural', 0)
      frappe.model.set_value(cdt, cdn, 'dissatisfied', 0)
      frappe.model.set_value(cdt, cdn, 'very_dissatisfied', 0)
    }
  },
  natural: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.natural === 1) {
      frappe.model.set_value(cdt, cdn, 'satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'very_satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'dissatisfied', 0)
      frappe.model.set_value(cdt, cdn, 'very_dissatisfied', 0)
    }
  },
  dissatisfied: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.dissatisfied === 1) {
      frappe.model.set_value(cdt, cdn, 'satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'natural', 0)
      frappe.model.set_value(cdt, cdn, 'very_satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'very_dissatisfied', 0)
    }
  },
  very_dissatisfied: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.very_dissatisfied === 1) {
      frappe.model.set_value(cdt, cdn, 'satisfied', 0)
      frappe.model.set_value(cdt, cdn, 'natural', 0)
      frappe.model.set_value(cdt, cdn, 'dissatisfied', 0)
      frappe.model.set_value(cdt, cdn, 'very_satisfied', 0)
    }
  },

  // customer feedback 2

  more_than_6_months: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.more_than_6_months === 1) {
      frappe.model.set_value(cdt, cdn, 'less_than_1_month', 0)
      frappe.model.set_value(cdt, cdn, 'never_used', 0)
      frappe.model.set_value(cdt, cdn, '_1_to_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'first_time_using_it', 0)
    }
  },
  less_than_1_month: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.less_than_1_month === 1) {
      frappe.model.set_value(cdt, cdn, 'more_than_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'never_used', 0)
      frappe.model.set_value(cdt, cdn, '_1_to_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'first_time_using_it', 0)
    }
  },
  _1_to_6_months: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item._1_to_6_months === 1) {
      frappe.model.set_value(cdt, cdn, 'more_than_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'never_used', 0)
      frappe.model.set_value(cdt, cdn, 'less_than_1_month', 0)
      frappe.model.set_value(cdt, cdn, 'first_time_using_it', 0)
    }
  },
  never_used: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.never_used === 1) {
      frappe.model.set_value(cdt, cdn, 'more_than_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'less_than_1_month', 0)
      frappe.model.set_value(cdt, cdn, '_1_to_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'first_time_using_it', 0)
    }
  },
  first_time_using_it: function (frm, cdt, cdn) {
    var item = locals[cdt][cdn]
    if (item.first_time_using_it === 1) {
      frappe.model.set_value(cdt, cdn, 'more_than_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'less_than_1_month', 0)
      frappe.model.set_value(cdt, cdn, '_1_to_6_months', 0)
      frappe.model.set_value(cdt, cdn, 'never_used', 0)
    }
  },
});
