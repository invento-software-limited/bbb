frappe.listview_settings["Customer Feedback"] = {
  // add_fields: ["status"],
	get_indicator: function (doc) {
    console.log(doc)
		if (doc.status === "Customer Feedback Collected") {
      console.log(doc.status)
			return [__("Customer Feedback Collected"), "orange", "status,=,Customer Feedback Collected"];
		} else if(doc.status === "Customer Feedback Collected"){
      return [__("Completed"), "green", "status,=,Completed"];
		}
	},
};
