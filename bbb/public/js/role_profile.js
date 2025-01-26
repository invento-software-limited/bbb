// Copyright (c) 2017, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Role Profile', {
	refresh: function(frm) {
		if (has_common(frappe.user_roles, ["Administrator", "System Manager", "Admin"])) {
			if (!frm.roles_editor) {
				const role_area = $(frm.fields_dict.roles_html.wrapper);
				frm.roles_editor = new frappe.RoleEditor(role_area, frm);
			}
			frm.roles_editor.show();

		}
	},

	validate: function(frm) {
		if (frm.roles_editor) {
			let checked_roles = frm.roles_editor.multicheck.selected_options
			if(has_common(frappe.user_roles, ["Administrator", "System Manager"]) && checked_roles.includes("System Manager")){
				frm.roles_editor.set_roles_in_table();
			}else{
				frm.roles_editor.multicheck.selected_options = checked_roles.filter(role => role !== "System Manager");
				frm.roles_editor.set_roles_in_table();
			}
		}
	}
});
