frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
		if (frm.doc.docstatus === 1 ) {
			frm.add_custom_button(__('Stock Distribution'), function() {
				frappe.model.open_mapped_doc({
					method: "bbb.bbb.controllers.utils.make_stock_distribution",
					frm: cur_frm,
				})
			}, __('Create'));
        }
	}
})