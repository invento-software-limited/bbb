// Copyright (c) 2022, Invento and contributors
// For license information, please see license.txt

frappe.ui.form.on('BI Attendance', {
	refresh: function(frm) {
        console.log("Refresh");

        frm.add_custom_button(__("Sync"), function (){
            frappe.call({
              method: "attendance.attendance.doctype.bi_attendance.api.get_attendance_data",
              args: {
                  "doc": frm.doc
              },
              callback: function(r) {
                 console.log(r.message);
              }
            }, ("Action"));
        });

    },
})