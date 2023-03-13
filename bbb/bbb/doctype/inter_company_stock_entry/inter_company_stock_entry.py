# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability


class ValidationError(frappe.ValidationError):
	pass

class InterCompanyStockEntry(Document):
	def validate(self):
		if self.source_company == self.target_company:
			frappe.throw(_("Please set different Company"), title=_("Validation Error"), exc=ValidationError)
			return False

		for index, item in enumerate(self.items):
			if item.qty < 1:
				frappe.throw(_("Row {}: Qty is mandatory".format(index+1)), title=_("Zero quantity"), exc=ValidationError)
				return False

			item_stock_qty, is_stock_item = get_stock_availability(item.item_code, self.source_warehouse)
			if item_stock_qty < item.qty:
				frappe.throw(_(f"Item Code: <b>{item.item_code}</b> is not available under warehouse <b>{self.source_warehouse}</b>. <br> The available qty is <b>{item_stock_qty}<b>"), title=_("Not Available"), exc=ValidationError)
				return False
			
		

	def before_submit(self):
		frappe.enqueue(make_stock_entry, doc=self, queue="long")
		# make_stock_entry(doc=self)
	
def make_stock_entry(doc):
	make_material_issue(doc)
	make_material_receipt(doc)

def make_material_issue(doc):

	stock_entry = frappe.new_doc('Stock Entry')
	stock_entry.company = doc.source_company
	stock_entry.from_warehouse = doc.source_warehouse
	stock_entry.stock_entry_type = 'Material Issue'
	stock_entry.purpose = 'Material Issue'
	stock_entry.set_posting_time = 1
	stock_entry.posting_date= doc.posting_date
	stock_entry.posting_time = doc.posting_time
	stock_entry.inter_company_stock_entry = doc.name
	stock_entry.remarks = doc.note
	for item in doc.items:
		stock_entry.append("items", {
			'item_code' : item.item_code,
			'qty' : item.qty,
			'basic_rate' : item.basic_rate,
			'stock_uom' : item.stock_uom,
			'uom': item.uom,
			's_warehouse': doc.source_warehouse
		})
	stock_entry.save()
	stock_entry.submit()

def make_material_receipt(doc):
	stock_entry = frappe.new_doc('Stock Entry')
	stock_entry.company = doc.target_company
	stock_entry.to_warehouse = doc.target_warehouse
	stock_entry.stock_entry_type = 'Material Receipt'
	stock_entry.purpose = 'Material Receipt'
	stock_entry.set_posting_time = 1
	stock_entry.posting_date= doc.posting_date
	stock_entry.posting_time = doc.posting_time
	stock_entry.inter_company_stock_entry = doc.name
	stock_entry.remarks = doc.note
	for item in doc.items:
		stock_entry.append("items", {
			'item_code' : item.item_code,
			'qty' : item.qty,
			'basic_rate' : item.basic_rate,
			'stock_uom' : item.stock_uom,
			'uom': item.uom,
			't_warehouse': doc.target_warehouse
		})
	stock_entry.save()
	stock_entry.submit()


		
