// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Inter Company Stock Entry', {
	refresh: (frm) => {
		//
	},
	setup: (frm, cdt, cdn) => {
        frm.set_query("source_warehouse", function() {
            return {
                "filters": {'company' : ["=", frm.doc.source_company]},
            };
        });

		frm.set_query("target_warehouse", function() {
            return {
                "filters": {'company' : ["=", frm.doc.target_company]},
            };
        });
    },

	source_company: (frm, cdt, cdn) => {
		frappe.model.set_value(cdt, cdn, 'source_warehouse', '')
	},

	target_company: (frm, cdt, cdn) => {
		frappe.model.set_value(cdt, cdn, 'target_warehouse', '')
	},

	validate: (frm, cdt, cdn) => {
		let total_qty = 0
		let total_amount = 0
		$.each(frm.doc.items,  function(i,  d) {
            // calculate qty and amount
            total_qty += d.qty
			total_amount+= d.amount
        });
		
		frappe.model.set_value(cdt, cdn, 'total_qty', total_qty ? total_qty : 0 )
		frappe.model.set_value(cdt, cdn, 'total_amount', total_amount ? total_amount : 0)
	},
});



frappe.ui.form.on('Inter Company Stock Entry Detail', {

	item_code: (frm, cdt, cdn) => {
		let item = locals[cdt][cdn];
		let parent = locals['Inter Company Stock Entry'][item.parent]

		if(!parent.source_company) {
			frappe.msgprint(__("Please specify source Company to proceed"));
		}

		if(!parent.source_warehouse) {
			frappe.msgprint(__("Please specify: Source Warehouse. It is needed to fetch Item Details."));
			return false
		}

		if(parent.source_warehouse) {
			let stock_detail = get_available_stock(item.item_code, parent.source_warehouse)
			let item_stock_qty = stock_detail[0]
			if(item_stock_qty < 1){
				let msg = "Item Code: <b>" + item.item_code + "</b> is not available under warehouse <b>" + parent.source_warehouse + "</b>."
				frappe.msgprint({
					title: __('Warning'),
					message: __(msg),
					indicator: 'red',
				});
				return false
			}
			
		}

		let amount = 1 * item.basic_rate
		frappe.model.set_value(cdt, cdn, 'qty', 1)
		frappe.model.set_value(cdt, cdn, 'amount', amount ? amount : 0)
	},

	qty: (frm, cdt, cdn) => {
		calculate_total(cdt, cdn)
	},

	basic_rate: (frm, cdt, cdn) => {
		calculate_total(cdt, cdn)
		
	},

});

const calculate_total = (cdt, cdn) => {
	let item = locals[cdt][cdn];
	let amount = item.qty * item.basic_rate
	frappe.model.set_value(cdt, cdn, 'amount', amount ? amount : 0)
}

const get_available_stock = (item_code, warehouse) => {
	var result = undefined
	frappe.call({
		method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
		async: false,
		args: {
			'item_code': item_code,
			'warehouse': warehouse,
		},
		callback(res) {
			result = res.message;
		}
	});
	return result
}