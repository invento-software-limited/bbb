frappe.listview_settings['Customer Requisition'] = {
    has_indicator_for_draft: true,
	get_indicator: function(doc) {
          var status_color = {
              0: "red",
              1: "green",
              2: "darkgrey"
          };
          var status = {
              0: "Draft",
              1: "Approved",
              2: "Cancelled"
          };
          return [__(status[doc.docstatus]), status_color[doc.docstatus], "status,=,"+status[doc.docstatus]];
	}
};