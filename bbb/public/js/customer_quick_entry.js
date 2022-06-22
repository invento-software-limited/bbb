frappe.provide('frappe.ui.form');

frappe.ui.form.CustomerQuickEntryForm = frappe.ui.form.QuickEntryForm.extend({
	init: function(doctype, after_insert, init_callback, doc, force) {
		this._super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	},

	render_dialog: function() {
		frappe.model.set_value('Customer', this.doc.name, 'mobile_number', this.doc.customer_name);
		frappe.model.set_value('Customer', this.doc.name, 'customer_name', null);
		this.mandatory = this.mandatory.concat(this.get_variant_fields());
		this._super();
	},
	get_variant_fields: function() {
		var variant_fields = [{
			fieldtype: "Section Break",
			label: __("Date Of Birth"),
			collapsible: 0
		},
		{
			label: __("Day"),
			fieldname: "day",
			fieldtype: "Int"
		},
		{
			fieldtype: "Column Break"
		},
		{
			label: __("Month"),
			fieldname: "month",
			fieldtype: "Select",
			options: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
		},
		{
			fieldtype: "Column Break"
		},
		{
			label: __("Year"),
			fieldname: "year",
			fieldtype: "Int"
		},];

		return variant_fields;
	},
});
