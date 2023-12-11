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
                if (d.qty > d.transfer_qty_from_stock_distribution) {
                    frappe.throw(`For Item <b>${d.item_code}</b> Accepted qty cannot greater then transfer qty`)
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
                if (d.qty > d.transfer_qty_from_stock_distribution) {
                    frappe.throw(`For Item <b>${d.item_code}</b> Accepted qty cannot greater then transfer qty`)
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
    // Get the child table data
    var items = frm.doc.items || [];

    // Iterate through the rows in reverse order
    for (var i = items.length - 1; i >= 0; i--) {
        var qty = flt(items[i].qty); // Assuming qty is a float field, adjust as needed

        // Remove the row if quantity is 0
        if (qty === 0) {
            frm.get_field('items').grid.grid_rows[i].remove();
        }
    }
}

cur_frm.cscript['Re-Create Stock'] = function() {
	frappe.model.open_mapped_doc({
		method: "bbb.bbb.controllers.utils.make_stock_entry",
		frm: cur_frm
	})
}