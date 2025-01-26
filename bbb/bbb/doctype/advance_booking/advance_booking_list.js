frappe.listview_settings['Advance Booking'] = {
    has_indicator_for_draft: true,
    // add_fields: ["status"],
  
      get_indicator: function(doc) {
          var status_color = {
              "Draft": "yellow",
              "To Deliver and Bill": "orange",
              "Completed": "green",
              "Submitted": "blue",
              "To Deliver": "darkgrey",
              "To Bill": "darkgrey",
              "Cancelled": "red"
  
          };
          return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
      },
      // right_column: "grand_total",
  };
  