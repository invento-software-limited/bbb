frappe.provide('erpnext.PointOfSale');
if(frappe.pages["parlour"]){
    frappe.pages['parlour'].on_page_load = function (wrapper) {
        frappe.ui.make_app_page({
            parent: wrapper,
            // title: __('Point of Sale'),
            single_column: true
        });

        frappe.require("parlour.bundle.js", function () {
            wrapper.pos = new erpnext.PointOfSale.Controller(wrapper);
            window.cur_pos = wrapper.pos;
        });
    };

    frappe.pages['parlour'].refresh = function (wrapper) {
        if (document.scannerDetectionData && wrapper.pos) {
            onScan.detachFrom(document);
            wrapper.pos.wrapper.html("");
            wrapper.pos.check_opening_entry();
        }
    };
}