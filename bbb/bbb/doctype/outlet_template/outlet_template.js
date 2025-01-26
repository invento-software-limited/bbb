// Copyright (c) 2023, invento software limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('Outlet Template', {
	validate: function(frm) {
		if (frm.doc.total_percentage !== 100) {
			frappe.throw(`Total Percentage Need To Be 100`)
		}
	}
});
frappe.ui.form.on('Outlet Selection Table', {
	percentage: function(frm){
		var total_percentage = 0;
        if (frm.doc.outlets){
            $.each(frm.doc.outlets, function(index, row){
                total_percentage += row.percentage || 0;
            });
        }
		frm.set_value("total_percentage",total_percentage)
	}
})
