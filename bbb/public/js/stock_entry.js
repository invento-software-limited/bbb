frappe.ui.form.on('Stock Entry', {

    onload: function(frm) {
        if (frm.doc.__islocal && frm.doc.stock_created_from){
            frappe.call ({
                method: "bbb.bbb.controllers.stock_entry.make_stock_entry",
                args : {
                    'name' : frm.doc.stock_created_from
                },
                freeze: true,
				freeze_message: __('Creating Stock Entry...'),
                callback: function(r){
                    r.message.forEach(function(row){
                        let tb_row = frm.add_child("items")
                        tb_row.item_code = row.item_code;
                        tb_row.transfer_qty_from_stock_distribution = row.transfer_qty_from_stock_distribution;
                        tb_row.qty = row.qty
                        tb_row.s_warehouse = row.s_warehouse
                        tb_row.t_warehouse = row.t_warehouse
                        tb_row.conversion_factor = row.conversion_factor
                        tb_row.uom = row.uom
                        tb_row.transfer_qty = row.transfer_qty
                    })
                    frm.refresh_field("items")
                }
            })
        }
    },
    refresh: function(frm){
        if (frm.doc.workflow_state === "Partially Completed" && frm.doc.stock_distribution && frm.doc.total_transfer_qty !== frm.doc.total_accepted_qty) {
            frm.add_custom_button(__("Re-Create Stock"), function(){
				frappe.model.with_doctype("Stock Entry", function() {
                    let stock_entry = frappe.model.get_new_doc("Stock Entry");
                    stock_entry.stock_created_from = frm.doc.name
                    stock_entry.stock_entry_type = frm.doc.stock_entry_type
                    stock_entry.from_warehouse = frm.doc.from_warehouse
                    stock_entry.to_warehouse = frm.doc.to_warehouse
                    frappe.set_route("Form", "Stock Entry", stock_entry.name);
                });
			});
		}
        setTimeout(() => {
            frm.remove_custom_button('Delivery Note','Get customers from');
            frm.remove_custom_button('Delivery Notes','View');
        }, 10);
        if ((frappe.user.has_role('Stock User') || frappe.user.has_role('Sales User'))) {
            setTimeout(() => {
                frm.remove_custom_button('Material Request','Create');
                frm.remove_custom_button('Purchase Invoice','Get Items From');
                frm.remove_custom_button('Material Request','Get Items From');
                frm.remove_custom_button('Bill of Materials','Get Items From');
            }, 10);
        }
    },
	before_workflow_action : function(frm) {
        let accepted_qty = 0;
        let transfered_qty = 0;
        if (frm.doc.items) {
            frm.doc.items.forEach((d) => {
                if (frm.doc.stock_distribution && !frm.doc.outgoing_stock_entry) {
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
                if (frm.doc.stock_distribution && !frm.doc.outgoing_stock_entry) {
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

        if (frm.doc.outgoing_stock_entry) {
            var items = []
            var dep = 0
            frm.doc.items.forEach((d) => {
                if (d.qty !== d.transfer_qty_from_stock_distribution) {
                    items.push(d.item_code)
                    dep += 1
                }
            })
            if (dep > 0) {
                frappe.throw({
                    title: __("Qty Message"),
                    message: __('In re-create stock, for Item <b>{0}</b> accepted and transfer qty must same.', [items.join(",")])
                });
            }
        }
    },
    // onload: function(frm) {
    //     // Call a function to remove rows with qty = 0
    //     removeRowsWithZeroQty(frm);
    //     if(frm.doc.__islocal) {
    //         frm.set_value("total_transfer_qty",0)
    //         frm.set_value("total_accepted_qty",0)
    //     }
        
    // }
});
