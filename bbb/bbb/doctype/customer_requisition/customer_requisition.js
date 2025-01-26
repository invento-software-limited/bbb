// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Customer Requisition', {
    // refresh: function(frm) {

    // }
    onload: function (frm) {
        // var btn_primary = document.getElementsByClassName('primary-action');
        // btn_primary[0].innerHTML = 'SS<span class="alt-underline">u</span>bmit'
        console.log(frm)
        frm.action_perm_type_map = {
            'Amend': "amend",
            'Cancel': "cancel",
            'Create': "create",
            'Delete': "delete",
            'Save': "write",
            'Submit': "submit",
            'Update': "submit"
        }
        if (!frm.doc.branch) {
            frappe.call("erpnext.selling.page.point_of_sale.point_of_sale.check_opening_entry", {"user": frappe.session.user}).then((r) => {
                if (r.message.length) {
                    frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'branch', r.message[0].pos_profile)
                    $.each(frm.doc.customer_requisition_items, function (i, d) {
                        d.branch = r.message[0].pos_profile
                    });
                } else {
                    frappe.call("bbb.bbb.doctype.customer_requisition.customer_requisition.get_pos_profile").then((r) => {
                        frappe.model.set_value(frm.doc.doctype, frm.doc.name, 'branch', r.message[0].name)
                        $.each(frm.doc.customer_requisition_items, function (i, d) {
                            d.branch = r.message[0].name
                        });
                    })
                }
            })
        }
    },
});
frappe.ui.form.on('Customer Requisition Item', {
    item_code: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (frm.doc.branch) {
            row.branch = frm.doc.branch;
            refresh_field("branch", cdn, "customer_requisition_items");
        } else {
            frm.script_manager.copy_from_first_row("customer_requisition_items", row, ["branch"]);
        }
    },
});
