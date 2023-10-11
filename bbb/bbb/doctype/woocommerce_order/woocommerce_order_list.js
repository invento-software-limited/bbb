frappe.listview_settings['Woocommerce Order'] = {
    has_indicator_for_draft: true,
    // add_fields: ["status"],
  
      get_indicator: function(doc) {
          var status_color = {
              "Draft": "red",
              "Ordered": "green",
              "Submitted": "blue",
              "Fulfilled": "blue",
              "Cancelled": "red"
  
          };
          return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
      },
  };
  