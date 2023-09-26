# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class WoocommerceOrder(Document):
	def __init__(self, *args, **kwargs):
		super(WoocommerceOrder, self).__init__(*args, **kwargs)
		
        
	def validate(self):
		pass
