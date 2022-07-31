# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt
import time

import frappe
import openpyxl
import os
from frappe.model.document import Document
from frappe import enqueue
from frappe import _


class CustomerBulkImport(Document):
    pass


@frappe.whitelist()
def customer_bulk_import(doc_name):
    enqueue(
        'bbb.bbb.doctype.customer_bulk_import.customer_bulk_import.customer_bulk_import_xl',
        queue='long', timeout=20000,
        doc_name=doc_name)

    return {"message": "Import Started"}


@frappe.whitelist()
def customer_bulk_import_xl(doc_name):
    doc = frappe.get_doc('Customer Bulk Import', doc_name)
    site_name = frappe.local.site
    cur_dir = os.getcwd()
    xlsx = openpyxl.load_workbook(str(cur_dir) + '/' + str(site_name) + str(doc.customer_xl))
    sheet = xlsx.active
    data = sheet.rows
    i = 0
    for row in data:
        if i > 0:
            customer_new_doc = frappe.new_doc("Customer")
            customer_new_doc.customer_name = row[0].value
            customer_new_doc.mobile_number = row[2].value
            customer_new_doc.customer_type = row[3].value
            customer_new_doc.customer_group = row[4].value
            customer_new_doc.territory = row[5].value
            customer_new_doc.purchase_amount = row[6].value
            customer_new_doc.pos_profile = row[7].value
            customer_new_doc.save()
            customer_new_doc.customer_name = row[1].value
            customer_new_doc.save()

        i += 1
    return {"message": "Import Done"}
