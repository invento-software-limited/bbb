// Copyright (c) 2022, invento software limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Bulk Import', {
	start_upload: function (frm) {
		if (frm.doc.name) {
			frappe.call({
				method: "bbb.bbb.doctype.customer_bulk_import.customer_bulk_import.customer_bulk_import",
				args: {
					doc_name: frm.doc.name,
				},
				callback: function (r) {
					frappe.msgprint(r.message);
				}
			});
		}
		else{
		    frappe.msgprint("Save the document first");
		}

	},
});
