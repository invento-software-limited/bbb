# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerRequisition(Document):
    def on_submit(self):
        pass


@frappe.whitelist()
def get_pos_profile():
    pos_profile = frappe.db.sql(
        """ select pos_profile.name from `tabPOS Profile` pos_profile, `tabPOS Profile User` pos_profile_user where pos_profile_user.user = '%s' limit 1""" % frappe.session.user,
        as_dict=1)
    return pos_profile
