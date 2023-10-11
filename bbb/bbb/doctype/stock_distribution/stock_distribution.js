// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Stock Distribution', {
	refresh: function (frm){
        frm.set_query("against_purchase_receipt", function() {
            return {
                "filters": {'supplier' : ["=", frm.doc.supplier]},
            };
        });
    },
	validate:function(frm){
		var total_percentage = 0;
        if (frm.doc.outlet_selection_table){
            $.each(frm.doc.outlet_selection_table, function(index, row){
                total_percentage += row.percentage || 0;
            });
        }
		frm.set_value("total_percentage",total_percentage)
	},
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
							row.warehouse = item.warehouse;
							row.uom = item.uom
						});
						frm.refresh_field('purchase_distribution_items');
					}
				}
			});
		}
	},
	outlet_template: function(frm){
		if (frm.doc.outlet_template){
			frappe.call({
				method: 'bbb.bbb.doctype.stock_distribution.stock_distribution.get_outlet_items',
				args: {
					template: frm.doc.outlet_template
				},
				callback: function(response) {
					if (response.message) {
						frm.clear_table('outlet_selection_table');
						$.each(response.message, function(i, item) {
							var row = frappe.model.add_child(frm.doc, 'Outlet Selection Table', 'outlet_selection_table');
							row.warehouse = item.warehouse;
							row.percentage = item.percentage;
						});
						frm.refresh_field('outlet_selection_table');
					}
				}
			});
		}
	},
	outlet_selection_table:function(frm){
		var total_percentage = 0;
		if (frm.doc.outlet_selection_table){
			$.each(frm.doc.outlet_selection_table, function(index, row){
				console.log("ppp")
				total_percentage += row.percentage || 0;
			});
		}
		frm.set_value("total_percentage",total_percentage)
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
					}else{
						frm.set_value("against_purchase_receipt" , "")
						frappe.throw(`No Purchase Receipt Against ${frm.doc.purchase_order}`)
					}
				}
			});
		}else{
			frappe.throw("Please Select Purchase Order")
		}
	},
	download_distribute_excell: function(frm){
		var total_percentage = 0;
        if (frm.doc.outlet_selection_table){
            $.each(frm.doc.outlet_selection_table, function(index, row){
                total_percentage += row.percentage || 0;
            });
        }
		if (frm.doc.purchase_distribution_items && frm.doc.outlet_selection_table && total_percentage === 100){
			let url = `/api/method/bbb.bbb.doctype.stock_distribution.stock_distribution.distribution_excell_generate`;
			open_url_post(url, {"doc": frm.doc}, true);
		}else{
			frappe.throw("Total Distribution Percentage Not Equal 100 ")
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
		frm.set_value("total_percentage",total_percentage)
	}
})
