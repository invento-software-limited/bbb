# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class WoocommerceOrder(Document):
	def __init__(self, *args, **kwargs):
		super(WoocommerceOrder, self).__init__(*args, **kwargs)
        
	def validate(self):
		if self.woocommerce_status == 'processing' and self.docstatus == 1:
			self.status = 'Ordered'
		elif self.woocommerce_status == 'complete' and self.docstatus == 1:
			self.status = 'Fulfilled'