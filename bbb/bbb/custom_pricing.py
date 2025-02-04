import copy
import json
import re

import frappe
from frappe import _, throw
from frappe.utils import flt


@frappe.whitelist()
def apply_pricing_rule(args, doc=None):
	"""
	args = {
	        "items": [{"doctype": "", "name": "", "item_code": "", "brand": "", "item_group": ""}, ...],
	        "customer": "something",
	        "customer_group": "something",
	        "territory": "something",
	        "supplier": "something",
	        "supplier_group": "something",
	        "currency": "something",
	        "conversion_rate": "something",
	        "price_list": "something",
	        "plc_conversion_rate": "something",
	        "company": "something",
	        "transaction_date": "something",
	        "campaign": "something",
	        "sales_partner": "something",
	        "ignore_pricing_rule": "something"
	}
	"""

	if isinstance(args, str):
		args = json.loads(args)

	args = frappe._dict(args)


	if not args.transaction_type:
		set_transaction_type(args)

	# list of dictionaries
	out = []

	if args.get("doctype") == "Material Request":
		return out

	item_list = args.get("items")
	args.pop("items")

	item_code_list = tuple(item.get("item_code") for item in item_list)
	query_items = frappe.get_all(
		"Item",
		fields=["item_code", "has_serial_no"],
		filters=[["item_code", "in", item_code_list]],
		as_list=1,
	)
	serialized_items = dict()
	for item_code, val in query_items:
		serialized_items.setdefault(item_code, val)

	for item in item_list:
		args_copy = copy.deepcopy(args)
		args_copy.update(item)
		data = get_pricing_rule_for_item(args_copy, doc=doc)
		out.append(data)

	return out


def update_pricing_rule_uom(pricing_rule, args):
	child_doc = {"Item Code": "items", "Item Group": "item_groups", "Brand": "brands", "Tag": "tags"}.get(
		pricing_rule.apply_on
	)

	apply_on_field = frappe.scrub(pricing_rule.apply_on)

	for row in pricing_rule.get(child_doc):
		if row.get(apply_on_field) == args.get(apply_on_field):
			pricing_rule.uom = row.uom


def get_pricing_rule_for_item(args, doc=None, for_validate=False):
	from bbb.bbb.controllers.pricing_rule.utils import (
		get_applied_pricing_rules,
		get_pricing_rule_items,
		get_pricing_rules,
		get_product_discount_rule,
	)

	if isinstance(doc, str):
		doc = json.loads(doc)

	if doc:
		doc = frappe.get_doc(doc)

	if args.get("is_free_item") or args.get("parenttype") == "Material Request":
		return {}

	item_details = frappe._dict(
		{
			"doctype": args.doctype,
			"has_margin": False,
			"name": args.name,
			"free_item_data": [],
			"parent": args.parent,
			"parenttype": args.parenttype,
			"child_docname": args.get("child_docname"),
			"discount_percentage": 0.0,
			"discount_amount": 0,
		}
	)
	# item_tag = frappe.db.get_value("Item", args.get("item_code"), "price_rule_tag")
	# args.tag = item_tag

	if args.ignore_pricing_rule or not args.item_code:
		if frappe.db.exists(args.doctype, args.name) and args.get("pricing_rules"):
			item_details = remove_pricing_rule_for_item(
				args.get("pricing_rules"),
				item_details,
				item_code=args.get("item_code"),
				rate=args.get("price_list_rate"),
			)
		return item_details

	update_args_for_pricing_rule(args)

	pricing_rules = (
		get_applied_pricing_rules(args.get("pricing_rules"))
		if for_validate and args.get("pricing_rules")
		else get_pricing_rules(args, doc)
	)

	if pricing_rules:
		rules = []

		for pricing_rule in pricing_rules:
			if not pricing_rule:
				continue

			if isinstance(pricing_rule, str):
				pricing_rule = frappe.get_cached_doc("Pricing Rule", pricing_rule)
				update_pricing_rule_uom(pricing_rule, args)
				fetch_other_item = True if pricing_rule.apply_rule_on_other else False
				pricing_rule.apply_rule_on_other_items = (
					get_pricing_rule_items(pricing_rule, other_items=fetch_other_item) or []
				)

			if pricing_rule.coupon_code_based == 1:
				if not args.coupon_code:
					return item_details

				coupon_code = frappe.db.get_value(
					doctype="Coupon Code", filters={"pricing_rule": pricing_rule.name}, fieldname="name"
				)
				if args.coupon_code != coupon_code:
					continue

			if pricing_rule.get("suggestion"):
				continue

			item_details.validate_applied_rule = pricing_rule.get("validate_applied_rule", 0)
			item_details.price_or_product_discount = pricing_rule.get("price_or_product_discount")

			rules.append(get_pricing_rule_details(args, pricing_rule))

			if pricing_rule.mixed_conditions or pricing_rule.apply_rule_on_other:
				item_details.update(
					{
						"price_or_product_discount": pricing_rule.price_or_product_discount,
						"apply_rule_on": (
							frappe.scrub(pricing_rule.apply_rule_on_other)
							if pricing_rule.apply_rule_on_other
							else frappe.scrub(pricing_rule.get("apply_on"))
						),
					}
				)

				if pricing_rule.apply_rule_on_other_items:
					item_details["apply_rule_on_other_items"] = json.dumps(
						pricing_rule.apply_rule_on_other_items
					)

			if not pricing_rule.validate_applied_rule:
				if pricing_rule.price_or_product_discount == "Price":
					apply_price_discount_rule(pricing_rule, item_details, args)
				else:
					get_product_discount_rule(pricing_rule, item_details, args, doc)

		if not item_details.get("has_margin"):
			item_details.margin_type = None
			item_details.margin_rate_or_amount = 0.0

		item_details.has_pricing_rule = 1

		item_details.pricing_rules = frappe.as_json([d.pricing_rule for d in rules])

		if not doc:
			return item_details

	elif args.get("pricing_rules"):
		item_details = remove_pricing_rule_for_item(
			args.get("pricing_rules"),
			item_details,
			item_code=args.get("item_code"),
			rate=args.get("price_list_rate"),
		)

	return item_details


def update_args_for_pricing_rule(args):
	if not (args.item_group and args.brand):
		item = frappe.get_cached_value("Item", args.item_code, ("item_group", "brand", "price_rule_tag"))
		if not item:
			return

		args.item_group, args.brand, args.tag = item

		if not args.item_group:
			frappe.throw(_("Item Group not mentioned in item master for item {0}").format(args.item_code))

	if args.transaction_type == "selling":
		if args.customer and not (args.customer_group and args.territory):
			if args.quotation_to and args.quotation_to != "Customer":
				customer = frappe._dict()
			else:
				customer = frappe.get_cached_value("Customer", args.customer, ["customer_group", "territory"])

			if customer:
				args.customer_group, args.territory = customer

		args.supplier = args.supplier_group = None

	elif args.supplier and not args.supplier_group:
		args.supplier_group = frappe.get_cached_value("Supplier", args.supplier, "supplier_group")
		args.customer = args.customer_group = args.territory = None


def get_pricing_rule_details(args, pricing_rule):
	return frappe._dict(
		{
			"pricing_rule": pricing_rule.name,
			"rate_or_discount": pricing_rule.rate_or_discount,
			"margin_type": pricing_rule.margin_type,
			"item_code": args.get("item_code"),
			"child_docname": args.get("child_docname"),
		}
	)


def apply_price_discount_rule(pricing_rule, item_details, args):
	item_details.pricing_rule_for = pricing_rule.rate_or_discount

	if (pricing_rule.margin_type in ["Amount", "Percentage"] and pricing_rule.currency == args.currency) or (
		pricing_rule.margin_type == "Percentage"
	):
		item_details.margin_type = pricing_rule.margin_type
		item_details.has_margin = True

		if pricing_rule.apply_multiple_pricing_rules and item_details.margin_rate_or_amount is not None:
			item_details.margin_rate_or_amount += pricing_rule.margin_rate_or_amount
		else:
			item_details.margin_rate_or_amount = pricing_rule.margin_rate_or_amount

	if pricing_rule.rate_or_discount == "Rate":
		pricing_rule_rate = 0.0
		if pricing_rule.currency == args.currency:
			pricing_rule_rate = pricing_rule.rate

		# TODO https://github.com/frappe/erpnext/pull/23636 solve this in some other way.
		if pricing_rule_rate:
			is_blank_uom = pricing_rule.get("uom") != args.get("uom")
			# Override already set price list rate (from item price)
			# if pricing_rule_rate > 0
			item_details.update(
				{
					"price_list_rate": pricing_rule_rate
					* (args.get("conversion_factor", 1) if is_blank_uom else 1),
				}
			)
		item_details.update({"discount_percentage": 0.0})

	for apply_on in ["Discount Amount", "Discount Percentage"]:
		if pricing_rule.rate_or_discount != apply_on:
			continue

		field = frappe.scrub(apply_on)
		if pricing_rule.apply_discount_on_rate and item_details.get("discount_percentage"):
			# Apply discount on discounted rate
			item_details[field] += (100 - item_details[field]) * (pricing_rule.get(field, 0) / 100)
		elif args.price_list_rate:
			value = pricing_rule.get(field, 0)
			calculate_discount_percentage = False
			if field == "discount_percentage":
				field = "discount_amount"
				value = args.price_list_rate * (value / 100)
				calculate_discount_percentage = True

			if field not in item_details:
				item_details.setdefault(field, 0)

			item_details[field] += value if pricing_rule else args.get(field, 0)
			if calculate_discount_percentage and args.price_list_rate and item_details.discount_amount:
				item_details.discount_percentage = flt(
					(flt(item_details.discount_amount) / flt(args.price_list_rate)) * 100
				)
		else:
			if field not in item_details:
				item_details.setdefault(field, 0)

			item_details[field] += pricing_rule.get(field, 0) if pricing_rule else args.get(field, 0)


@frappe.whitelist()
def remove_pricing_rule_for_item(pricing_rules, item_details, item_code=None, rate=None):
	from erpnext.accounts.doctype.pricing_rule.utils import (
		get_applied_pricing_rules,
		get_pricing_rule_items,
	)

	if isinstance(item_details, str):
		item_details = json.loads(item_details)
		item_details = frappe._dict(item_details)

	for d in get_applied_pricing_rules(pricing_rules):
		if not d or not frappe.db.exists("Pricing Rule", d):
			continue
		pricing_rule = frappe.get_cached_doc("Pricing Rule", d)

		if pricing_rule.price_or_product_discount == "Price":
			if pricing_rule.rate_or_discount == "Discount Percentage":
				item_details.discount_percentage = 0.0
				item_details.discount_amount = 0.0
				item_details.rate = rate or 0.0

			if pricing_rule.rate_or_discount == "Discount Amount":
				item_details.discount_amount = 0.0

			if pricing_rule.margin_type in ["Percentage", "Amount"]:
				item_details.margin_rate_or_amount = 0.0
				item_details.margin_type = None
		elif pricing_rule.get("free_item"):
			item_details.remove_free_item = (
				item_code if pricing_rule.get("same_item") else pricing_rule.get("free_item")
			)

		if pricing_rule.get("mixed_conditions") or pricing_rule.get("apply_rule_on_other"):
			items = get_pricing_rule_items(pricing_rule, other_items=True)
			item_details.apply_on = (
				frappe.scrub(pricing_rule.apply_rule_on_other)
				if pricing_rule.apply_rule_on_other
				else frappe.scrub(pricing_rule.get("apply_on"))
			)
			item_details.applied_on_items = ",".join(items)

	item_details.pricing_rules = ""
	item_details.pricing_rule_removed = True

	return item_details


def set_transaction_type(args):
	if args.transaction_type:
		return
	if args.doctype in ("Opportunity", "Quotation", "Sales Order", "Delivery Note", "Sales Invoice"):
		args.transaction_type = "selling"
	elif args.doctype in (
		"Material Request",
		"Supplier Quotation",
		"Purchase Order",
		"Purchase Receipt",
		"Purchase Invoice",
	):
		args.transaction_type = "buying"
	elif args.customer:
		args.transaction_type = "selling"
	else:
		args.transaction_type = "buying"


