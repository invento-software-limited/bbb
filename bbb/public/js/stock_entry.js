frappe.ui.form.on('Stock Entry', {
    refresh: function(frm){
        if (frm.doc.docstatus === 1 && frm.doc.total_transfer_qty !== frm.doc.total_accepted_qty) {
            frm.add_custom_button(__('Re-Create Stock'),
                cur_frm.cscript['Re-Create Stock']
			);
		}
        setTimeout(() => {
            frm.remove_custom_button('Delivery Note','Get customers from');
            frm.remove_custom_button('Delivery Notes','View');
        }, 10);
    },
	before_workflow_action : function(frm) {
        let accepted_qty = 0;
        let transfered_qty = 0;
        if (frm.doc.items) {
            frm.doc.items.forEach((d) => {
                if (frm.doc.stock_distribution) {
                    if (d.qty > d.transfer_qty_from_stock_distribution) {
                        frappe.throw(`For Item <b>${d.item_code}</b> Accepted qty cannot greater then transfer qty`)
                    }
                }
                accepted_qty += d.qty
                transfered_qty += d.transfer_qty_from_stock_distribution
            })
        }
        frm.set_value("total_transfer_qty",transfered_qty)
        frm.set_value("total_accepted_qty",accepted_qty)
    },
    validate: function(frm) {
        let accepted_qty = 0;
        let transfered_qty = 0;
        if (frm.doc.items) {
            frm.doc.items.forEach((d) => {
                if (frm.doc.stock_distribution) {
                    if (d.qty > d.transfer_qty_from_stock_distribution) {
                        frappe.throw(`For Item <b>${d.item_code}</b> Accepted qty cannot greater then transfer qty`)
                    }
                }
                accepted_qty += d.qty
                transfered_qty += d.transfer_qty_from_stock_distribution
            })
        }
        frm.set_value("total_transfer_qty",transfered_qty)
        frm.set_value("total_accepted_qty",accepted_qty)
    },
    onload: function(frm) {
        // Call a function to remove rows with qty = 0
        removeRowsWithZeroQty(frm);
    }
});

function removeRowsWithZeroQty(frm) {
    console.log("oooo")
    var items = frm.doc.items || [];

    for (var i = items.length - 1; i >= 0; i--) {
        var qty = flt(items[i].qty);
        if (qty === 0) {
            frm.get_field('items').grid.grid_rows[i].remove();
            frm.refresh_field("items");
        }
    }
}

cur_frm.cscript['Re-Create Stock'] = function() {
	frappe.model.open_mapped_doc({
		method: "bbb.bbb.controllers.utils.make_stock_entry",
		frm: cur_frm
	})
}