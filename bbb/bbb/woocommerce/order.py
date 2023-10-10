import base64
import hashlib
import hmac
import json

import frappe
from frappe import _
from frappe.utils import cstr
import frappe.utils
from frappe import _
from frappe.utils import cint, cstr, flt, nowdate, nowtime
from six import string_types

from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.stock_ledger import make_sl_entries


@frappe.whitelist(allow_guest=True)
def update_or_cancel(*args, **kwargs):
	bbb_settings = frappe.get_doc("BBB Settings")
	if bbb_settings.woocommerce_status == "Disabled":
		return
	try:
		order(*args, **kwargs)
	except Exception:
		error_message = (
			frappe.get_traceback() + "\n\n Request Data: \n" + json.loads(frappe.request.data).__str__()
		)
		frappe.log_error(error_message, "WooCommerce Error")
		raise

def verify_request():
	woocommerce_settings = frappe.get_doc("Woocommerce Settings")
	sig = base64.b64encode(
		hmac.new(
			woocommerce_settings.secret.encode("utf8"), frappe.request.data, hashlib.sha256
		).digest()
	)

	if (
		frappe.request.data
		and not sig == frappe.get_request_header("X-Wc-Webhook-Signature", "").encode()
	):
		frappe.throw(_("Unverified Webhook Data"))
	frappe.set_user(woocommerce_settings.creation_user)
 
@frappe.whitelist()
def order(*args, **kwargs):
	if frappe.request and frappe.request.data:
		verify_request()
		try:
			order = json.loads(frappe.request.data)
		except ValueError:
			# woocommerce returns 'webhook_id=value' for the first request which is not JSON
			order = frappe.request.data
		status = order.get('status')
		items = order.get('line_items')

		if status in ['processing', 'cancelled', 'delivered']:
			doc = create_woocommerce_order(order)
			if status != 'delivered':
				sle = update_stock_ledger(items, status, doc)
				frappe.db.commit()
				return sle

def create_woocommerce_order(order):
	wc_status = {'processing': "Ordered", 'cancelled': 'Cancelled', 'delivered': 'Fulfilled'}
	try:
		doc = frappe.get_doc('Woocommerce Order', {'woocommerce_id': str(order.get('id'))})
		doc.status = wc_status.get(order.get('status'))
		doc.save()
			
	except:
		doc = frappe.new_doc("Woocommerce Order")
		doc.woocommerce_id = order.get('id')
		doc.parent_id = order.get('parent_id')
		doc.posting_date = nowdate()
		doc.posting_time = nowtime()
		doc.json_data = json.dumps(order)
		doc.woocommerce_status = order.get('status')
		doc.insert()
		# doc.save()
		doc.submit()
		return doc

def update_stock_ledger(items, status, doc):
	sl_entries = []
	# Loop over items and packed items table
	items = get_item_list(items, status, doc)
	for d in items:
		if flt(d.conversion_factor) == 0.0:
			d.conversion_factor = (
				get_conversion_factor(d.item_code, d.uom).get("conversion_factor") or 1.0
			)

		# On cancellation or return entry submission, make stock ledger entry for
		# target warehouse first, to update serial no values properly
		if d.warehouse:
			sl_entries.append(get_sle_for_source_warehouse(d))
		elif d.target_warehouse:
			sl_entries.append(get_sle_for_target_warehouse(d))
	
	sle = make_sl_entries(sl_entries)
	return sle
	


def get_item_list(items, status, doc):
	woocommerce_settings = frappe.get_doc("Woocommerce Settings")
	default_source_warehouse, default_target_warehouse = woocommerce_settings.warehouse, woocommerce_settings.warehouse
	il = []
	for d in items:
		item = search_for_woocommerce_id_or_sku_or_barcode_number(d.get('product_id'), d.get('sku'))
		
		if status == 'processing' and item:
			il.append(
				frappe._dict(
					{
						"warehouse": default_source_warehouse,
						"item_code": item.get('item_code'),
						"qty": flt(d.get('quantity')),
						"uom": item.get('stock_uom'),
						"stock_uom": item.get('stock_uom'),
						"conversion_factor": 0.0,
						"batch_no": None,
						"serial_no": None,
						"target_warehouse": '',
						"company": frappe.defaults.get_user_default("company"),
						"voucher_type": 'Woocommerce Order',
						"voucher_no": doc.name,
						"voucher_detail_no": doc.name,
						"allow_zero_valuation": 0,
						"incoming_rate": d.get("price")
					}
				)
			)
		elif status == 'cancelled' and item:
			il.append(
				frappe._dict(
					{
						"warehouse": '',
						"item_code": item.get('item_code'),
						"qty": flt(d.get('quantity')),
						"uom": item.get('stock_uom'),
						"stock_uom": item.get('stock_uom'),
						"conversion_factor": 0.0,
						"batch_no": None,
						"serial_no": None,
						"target_warehouse": default_target_warehouse,
						"company": frappe.defaults.get_user_default("company"),
						"voucher_type": 'Woocommerce Order',
						"voucher_no": doc.name,
						"voucher_detail_no": doc.name,
						"allow_zero_valuation": 0,
						"incoming_rate": d.get("price")
					}
				)
			)
	return il


def get_sle_for_source_warehouse(item_row):
	sle = get_sl_entries(
		item_row,
		{
			"actual_qty": -1 * flt(item_row.qty),
			"incoming_rate": item_row.incoming_rate,
			"recalculate_rate": 1,
		},
	)
	return sle

def get_sle_for_target_warehouse(item_row):
	sle = get_sl_entries(
		item_row, {"actual_qty": flt(item_row.qty), "warehouse": item_row.target_warehouse}
	)
	return sle

def get_sl_entries(d, args):
	valuation_rate = frappe.db.get_value('Item', d.get('item_code'), 'valuation_rate')

	sl_dict = frappe._dict(
		{
			"item_code": d.get("item_code", None),
			"warehouse": d.get("warehouse", None),
			"posting_date": nowdate(),
			"posting_time": nowtime(),
			"fiscal_year": get_fiscal_year(nowdate(), company=d.get('company'))[0],
			"voucher_type": 'Woocommerce Order',
			"voucher_no": d.get('voucher_no'),
			"voucher_detail_no": d.get('voucher_no'),
			"actual_qty": args.get('actual_qty'),
			"stock_uom": frappe.db.get_value(
				"Item", args.get("item_code") or d.get("item_code"), "stock_uom"
			),
			"incoming_rate": 0,
			"valuation_rate": valuation_rate,
			"company": d.get('company'),
			"batch_no": cstr(d.get("batch_no")).strip(),
			"serial_no": d.get("serial_no"),
			"is_cancelled": 0,
		}
	)
	sl_dict.update(args)
	return sl_dict


def search_for_woocommerce_id_or_sku_or_barcode_number(search_value, sku):
	from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability
 
	# search woocommerce id
	item_code = frappe.db.get_value('Item', {'woocommerce_id': search_value}, 'item_code', as_dict=True)

	# search sku
	if not item_code:
		item_code = frappe.db.get_value('Item', {'sku': sku}, 'item_code', as_dict=True)
	
	# search barcode no
	if not item_code:
		item_code = frappe.db.get_value(
			"Item Barcode", {"barcode": search_value}, ["barcode", "parent as item_code"], as_dict=True
		)

 	# search item code
	if not item_code:
		item_code = frappe.db.get_value(
			"Item", {"item_code": search_value}, ["item_code"], as_dict=True
		)


	if item_code:
		item_info = frappe.db.get_value(
			"Item",
			item_code,
			[
				"name as item_code",
				"is_stock_item",
				"stock_uom"
			],
			as_dict=1,
		)
		return item_info

	return {}