# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe.utils import flt


from erpnext.stock.doctype.stock_ledger_entry.stock_ledger_entry import StockLedgerEntry


class CustomStockLedgerEntry(StockLedgerEntry):
	def __init__(self, *args, **kwargs):
		super(CustomStockLedgerEntry, self).__init__(*args, **kwargs)
  
  
	def on_update(self):
		# super(CustomStockLedgerEntry, self).on_submit()
  
		woocommerce_settings = frappe.get_doc("Woocommerce Settings")
		item_doc = frappe.get_doc('Item', {'item_code': self.item_code})

		if item_doc.woocommerce_id and woocommerce_settings.warehouse == self.warehouse:
			from woocommerce import API
			wcapi = API(
				url=woocommerce_settings.woocommerce_server_url,
				consumer_key=woocommerce_settings.api_consumer_key,
				consumer_secret=woocommerce_settings.api_consumer_secret,
				wp_api=True,
				version="wc/v3",
				query_string_auth=True,
			)
			data = {
				"stock_quantity": self.qty_after_transaction,
				"manage_stock": True
			}
			url = "products/" + str(item_doc.woocommerce_id)
			wcapi.put(url, data).json()