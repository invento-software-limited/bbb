// Copyright (c) 2022, Invento and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance API Config', {
	refresh: function(frm) {
        frm.add_custom_button(__("Sync"), function (){
            frappe.call({
              // method: "attendance.attendance.doctype.bi_attendance.api.get_attendance_data",
              method: "attendance_sync.erpnext_sync.sync_biometric_attendance",
              args: {
                  "doc": frm.doc
              },
              callback: function(r) {
                 console.log(r.message);
              }
            }, ("Action"));
        });
	}
});
