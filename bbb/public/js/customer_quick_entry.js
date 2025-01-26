frappe.provide('frappe.ui.form');


frappe.ui.form.CustomerQuickEntryForm = frappe.ui.form.QuickEntryForm.extend({
	init: function(doctype, after_insert, init_callback, doc, force) {
		this._super(doctype, after_insert, init_callback, doc, force);
		this.skip_redirect_on_error = true;
	},

	render_dialog: function() {
		frappe.model.set_value('Customer', this.doc.name, 'mobile_number', this.doc.customer_name);
		frappe.model.set_value('Customer', this.doc.name, 'customer_name', null);
		// this.mandatory = this.mandatory.concat(this.get_variant_fields());
		this.mandatory = this.get_variant_fields();

		this._super();
	},
	get_variant_fields: function() {
		var variant_fields = [
		{
			label: __("Full Name"),
			fieldname: "customer_name",
			fieldtype: "Data",
			reqd:1
		},
		{
			fieldtype: "Column Break"
		},
		{
			label: __("Mobile Number"),
			fieldname: "mobile_number",
			fieldtype: "Data",
			reqd:1
		},
		{
			fieldtype: "Section Break",
			collapsible: 0
		},
		{
			label: __("Source"),
			fieldname: "source",
			fieldtype: "Link",
			options: "Customer Source",
		},
		{
			fieldtype: "Column Break"
		},
		{
			label: __("Customer Group"),
			fieldname: "customer_group",
			fieldtype: "Link",
			options: "Customer Group",
		},
		{
			fieldtype: "Section Break",
			collapsible: 0
		},
		{
			fieldtype: "Section Break",
			label: __("Date Of Birth"),
			collapsible: 0
		},
		{
			label: __("Day"),
			fieldname: "birth_day",
			fieldtype: "Int"
		},
		{
			fieldtype: "Column Break"
		},
		{
			label: __("Month"),
			fieldname: "birth_month",
			fieldtype: "Int",
			// options: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
		},
		{
			fieldtype: "Column Break"
		},
		{
			label: __("Year"),
			fieldname: "birth_year",
			fieldtype: "Int"
		},
		{
			fieldtype: "Section Break",
			collapsible: 0
		},
		{
			label: __("Territory"),
			fieldname: "territory",
			fieldtype: "Link",
			options: "Territory",
			reqd:1
		},

		];

		return variant_fields;
	},

	register_primary_action: function (){
		const me = this;
		this.dialog.set_primary_action(__('Save'), function() {
			let regex = new RegExp('^01\\d{9}$');
			if(regex.test(this.doc.mobile_number) === false){
				frappe.throw(__('Please enter 11 digit mobile number. Do not include country code(+88). Ex- 01700000000, 01300000000'));
				return;
			}
			if(me.dialog.working) {
				return;
			}
			var data = me.dialog.get_values();

			if(data) {
				me.dialog.working = true;
				me.dialog.set_message(__('Saving...'));
				me.insert().then(() => {
					me.dialog.clear_message();
				});
			}
		});
	}
});
