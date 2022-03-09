frappe.listview_settings['Employee Checkin'] = {
    onload: function(listView) {
        listView.page.add_action_icon(__("Sync Attendance"), function() {
            frappe.call({
              method: "attendance_sync.erpnext_sync.sync_biometric_attendance",
              args: {},
              callback: function(r) {
                 console.log(r.message);
              }
            }, ("Action"));
        });
	}
};