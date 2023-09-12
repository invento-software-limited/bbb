// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Distribution', {
	get_items_to_distribute: function(frm){
		if (frm.doc.purchase_order){
			frappe.call({
				method: 'bbb.bbb.doctype.stock_distribution.stock_distribution.get_purchase_order_items',
				args: {
					po_number: frm.doc.purchase_order
				},
				callback: function(response) {
					if (response.message) {
						frm.clear_table('purchase_distribution_items');
						$.each(response.message, function(i, item) {
							var row = frappe.model.add_child(frm.doc, 'Purchase Distribution Item', 'purchase_distribution_items');
							row.item_code = item.item_code;
							row.item_name = item.item_name;
							row.qty = item.qty;
							row.rate = item.rate;
						});
						frm.refresh_field('purchase_distribution_items');
					}
				}
			});
		}
	},
	get_purchase_receipt:function(frm){
		if (frm.doc.purchase_order){
			frappe.call({
				method: 'bbb.bbb.doctype.stock_distribution.stock_distribution.get_purchase_receipt',
				args: {
					purchase_order: frm.doc.purchase_order
				},
				callback: function(response) {
					if (response.message) {
						frm.set_value("against_purchase_receipt" , response.message)
					}
				}
			});
		}else{
			frappe.throw("Please Select Purchase Order")
		}
	},
	download_distribute_excell: function(frm){
		if (frm.doc.purchase_distribution_items && frm.doc.outlet_selection_table){
			let url = `/api/method/bbb.bbb.doctype.stock_distribution.stock_distribution.distribution_excell_generate`;
			open_url_post(url, {"doc": frm.doc}, true);
		}
	},
	match_with_receipt:function(frm){
		if (frm.doc.upload_distribution_excell && frm.doc.against_purchase_receipt){
			frappe.call({
				method: 'bbb.bbb.doctype.stock_distribution.stock_distribution.validate_qty_excell_data',
				args: {
					file_url: frm.doc.upload_distribution_excell,
					pr : frm.doc.against_purchase_receipt
				},
			});
		}else{
			frappe.throw("Please Upload Distribution excell And Set Against Purchase Receipt")
		}
	}
});

frappe.ui.form.on('Outlet Selection Table', {
	percentage: function(frm){
		var total_percentage = 0;
        if (frm.doc.outlet_selection_table){
            $.each(frm.doc.outlet_selection_table, function(index, row){
                total_percentage += row.percentage || 0;
            });
        }
		var ext = 100 - total_percentage
		if (total_percentage !== 100) {
			frappe.msgprint(`Need ${ext} to complete percentage`)
		}
	}
})
