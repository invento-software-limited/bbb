frappe.provide('erpnext.PointOfSale');
// frappe.pages['bbb-restaurant'].on_page_load = function(wrapper) {
//     frappe.require("assets/bbb/css/restaurant-pos.css");
//     frappe.ui.make_app_page({
//         parent: wrapper,
//         // title: __('Point of Sale'),
//         single_column: true
//     });
//     frappe.require("assets/js/restaurant.min.js", function () {
//         wrapper.pos = new erpnext.PointOfSale.Controller(wrapper);
//         window.cur_pos = wrapper.pos;
//     });
// }

// frappe.pages['bbb-restaurant'].refresh = function (wrapper) {
//     if (document.scannerDetectionData) {
//         onScan.detachFrom(document);
//         wrapper.pos.wrapper.html("");
//         wrapper.pos.check_opening_entry();
//     }
// };
