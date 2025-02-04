# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe.utils import flt


from erpnext.stock.doctype.stock_ledger_entry.stock_ledger_entry import StockLedgerEntry
from woocommerceconnector.woocommerce_requests import put_request

class CustomStockLedgerEntry(StockLedgerEntry):
	def __init__(self, *args, **kwargs):
		super(CustomStockLedgerEntry, self).__init__(*args, **kwargs)
  
  
	def on_update(self):
		# super(CustomStockLedgerEntry, self).on_submit()
  
		woocommerce_settings = frappe.get_doc("WooCommerce Config")
		item_doc = frappe.get_doc('Item', {'item_code': self.item_code})

		if item_doc.woocommerce_id and woocommerce_settings.warehouse == self.warehouse:
			data = {
				"stock_quantity": self.qty_after_transaction,
				"manage_stock": True
			}
			put_request("products/" + str(item_doc.woocommerce_id),data)
