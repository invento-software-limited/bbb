frappe.provide('frappe.ui.form');

frappe.ui.form.CustomerQuickEntryForm = frappe.ui.form.QuickEntryForm.extend({
	init: function(doctype, after_insert, init_callback, doc, force) {
		this._super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	},

	render_dialog: function() {
		frappe.model.set_value('Customer', this.doc.name, 'mobile_number', this.doc.customer_name);
		frappe.model.set_value('Customer', this.doc.name, 'customer_name', null);
		this._super();
	},
});
