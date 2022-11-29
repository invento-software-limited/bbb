frappe.ui.form.off("POS Closing Entry", "pos_opening_entry");
frappe.ui.form.on('POS Closing Entry', {
    onload:function(frm){
        frm.set_df_property('period_end_date', 'read_only', 0)
    },
    pos_opening_entry:function(frm) {
		if (frm.doc.pos_opening_entry && frm.doc.period_start_date && frm.doc.period_end_date && frm.doc.user) {
			reset_values(frm);
			frm.trigger("set_opening_amounts");
			frm.trigger("get_pos_invoices_");
		}
	},

	set_opening_amounts(frm) {
		frappe.db.get_doc("POS Opening Entry", frm.doc.pos_opening_entry)
			.then(({ balance_details }) => {
				balance_details.forEach(detail => {
					frm.add_child("payment_reconciliation", {
						mode_of_payment: detail.mode_of_payment,
						opening_amount: detail.opening_amount,
						expected_amount: detail.opening_amount
					});
				})
			});
	},

	get_pos_invoices_(frm) {
		frappe.call({
			method: 'bbb.bbb.pos_closing_entry.get_pos_invoices',
			args: {
				start: frappe.datetime.get_datetime_as_string(frm.doc.period_start_date),
				end: frappe.datetime.get_datetime_as_string(frm.doc.period_end_date),
				pos_profile: frm.doc.pos_profile,
				user: frm.doc.user
			},
			callback: (r) => {
				let pos_docs = r.message;
				set_form_data(pos_docs, frm);
				refresh_fields(frm);
				set_html_data(frm);
			}
		});
	},
})