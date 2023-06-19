frappe.ui.form.off("POS Closing Entry", "pos_opening_entry");
frappe.ui.form.on('POS Closing Entry', {
    onload:function(frm){
        frm.set_df_property('period_end_date', 'read_only', 0)
    },
    pos_opening_entry:function(frm) {
		if (frm.doc.pos_opening_entry && frm.doc.period_start_date && frm.doc.period_end_date && frm.doc.user) {
			reset_values(frm);
			frm.trigger("get_pos_invoices_");
			frm.trigger("get_advance_booking");
		}
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

	get_advance_booking(frm) {
		frm.set_value("advance_booking_reference", []);
		frappe.call({
			method: 'bbb.bbb.pos_closing_entry.get_advance_booking',
			args: {
				start: frappe.datetime.get_datetime_as_string(frm.doc.period_start_date),
				end: frappe.datetime.get_datetime_as_string(frm.doc.period_end_date),
				pos_profile: frm.doc.pos_profile,
				user: frm.doc.user
			},
			callback: (r) => {
				let pos_docs = r.message;
				set_advance_booking_data(pos_docs, frm);
				refresh_fields(frm);
			}
		});
	},
	before_save: function(frm) {
		frm.set_value("grand_total", 0);
		frm.set_value("net_total", 0);
		frm.set_value("total_quantity", 0);
		frm.set_value("total_advance_booking", 0);
		frm.set_value("total_advance_paid", 0);
		frm.set_value("total_due", 0);
		frm.set_value("total_advance_quantity", 0);
		frm.set_value("taxes", []);

		for (let row of frm.doc.payment_reconciliation) {
			row.expected_amount = row.opening_amount;
		}

		for (let row of frm.doc.pos_transactions) {
			frappe.db.get_doc("POS Invoice", row.pos_invoice).then(doc => {
				frm.doc.grand_total += flt(doc.grand_total);
				frm.doc.net_total += flt(doc.net_total);
				frm.doc.total_quantity += flt(doc.total_qty);
				refresh_payments(doc, frm);
				refresh_taxes(doc, frm);
				refresh_fields(frm);
				set_html_data(frm);
			});
		}
		for (let row of frm.doc.advance_booking_reference) {
			frappe.db.get_doc("Advance Booking", row.advance_booking).then(doc => {
				frm.doc.total_advance_booking += flt(doc.rounded_total);
				frm.doc.total_advance_paid += flt(doc.total_advance);
				frm.doc.total_due += flt(doc.outstanding_amount);
				frm.doc.total_advance_quantity += flt(doc.total_qty);
				refresh_fields(frm);
			});
		}
	}
	
})

function set_advance_booking_data(data, frm) {
	data.forEach(d => {
		add_to_advance_booking(d, frm);
		refresh_advance_payments(d, frm);
		refresh_fields(frm);
	});
}

function add_to_advance_booking(d, frm) {
	console.log(d.name)
	frm.add_child("advance_booking_reference", {
		advance_booking: d.name,
		posting_date: d.posting_date,
		customer: d.customer,
		grand_total: d.grand_total,
		rounded_total: d.rounded_total,
		total_advance: d.total_advance,
		outstanding_amount: d.outstanding_amount,
	})
	frm.refresh_fields()

}

function refresh_advance_payments(d, frm) {
	d.payments.forEach(p => {
		const payment = frm.doc.payment_reconciliation.find(pay => pay.mode_of_payment === p.mode_of_payment);
		if (p.account == d.account_for_change_amount) {
			p.amount -= flt(d.change_amount);
		}
		if (payment) {
			payment.expected_amount += flt(p.total_advance);
			payment.difference = payment.closing_amount - payment.expected_amount;
		} else {
			frm.add_child("payment_reconciliation", {
				mode_of_payment: p.mode_of_payment,
				opening_amount: 0,
				expected_amount: p.total_advance,
				closing_amount: 0
			})
		}
	})
}
