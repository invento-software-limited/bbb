// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Service Record'] = {
  has_indicator_for_draft: true,
  // add_fields: ["status"],

	get_indicator: function(doc) {
		var status_color = {
			"Draft": "yellow",
			"Pending For Service": "orange",
			"In Progress": "green",
			"Submitted": "blue",
			"Consolidated": "green",
			"Paused": "darkgrey",
			"Cancelled": "red"

		};
		return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
	},
	// right_column: "grand_total",
};
