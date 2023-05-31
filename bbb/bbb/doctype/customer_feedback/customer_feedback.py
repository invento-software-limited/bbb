# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class CustomerFeedback(Document):
    def before_submit(self):
        if self.status != 'Completed':
            frappe.throw(_("You can submit this document after complete customer feedback"))
