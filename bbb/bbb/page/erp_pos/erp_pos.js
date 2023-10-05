// frappe.pages['erp-pos'].on_page_load = function(wrapper) {
// 	var page = frappe.ui.make_app_page({
// 		parent: wrapper,
// 		title: 'ERP POS',
// 		single_column: true
// 	});
// }


frappe.provide('erpnext.PointOfSale');

frappe.pages['erp-pos'].on_page_load = function(wrapper) {
	frappe.require("assets/bbb/css/erp-pos.css");
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Point of Sale'),
		single_column: true
	});

	frappe.require('assets/js/erp-pos.js', function() {
		wrapper.pos = new erpnext.PointOfSale.Controller(wrapper);
		window.cur_pos = wrapper.pos;
	});
};

frappe.pages['erp-pos'].refresh = function(wrapper) {
	if (document.scannerDetectionData) {
		onScan.detachFrom(document);
		wrapper.pos.wrapper.html("");
		wrapper.pos.check_opening_entry();
	}
};