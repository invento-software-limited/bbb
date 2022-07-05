# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
import datetime
from frappe import _
from frappe.utils import cint, flt, get_link_to_form, getdate, nowdate

from erpnext.accounts.doctype.pricing_rule.utils import (
    apply_pricing_rule_for_free_items,
    apply_pricing_rule_on_transaction,
    get_applied_pricing_rules,
)

from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice


class CustomPOSInvoice(POSInvoice):
    def __init__(self, *args, **kwargs):
        super(CustomPOSInvoice, self).__init__(*args, **kwargs)

    def apply_pricing_rule_on_items(self, item, pricing_rule_args):
        if not pricing_rule_args.get("validate_applied_rule", 0):
            # if user changed the discount percentage then set user's discount percentage ?
            if pricing_rule_args.get("price_or_product_discount") == "Price":
                item.set("pricing_rules", pricing_rule_args.get("pricing_rules"))
                item.set("discount_percentage", pricing_rule_args.get("discount_percentage"))
                item.set("discount_amount", pricing_rule_args.get("discount_amount"))
                if pricing_rule_args.get("pricing_rule_for") == "Rate":
                    item.set("price_list_rate", pricing_rule_args.get("price_list_rate"))

                if item.get("price_list_rate"):
                    item.rate = flt(
                        item.price_list_rate * (1.0 - (flt(item.discount_percentage) / 100.0)),
                        item.precision("rate"),
                    )

                    if item.get("discount_amount"):
                        item.rate = item.price_list_rate - item.discount_amount

                if item.get("apply_discount_on_discounted_rate") and pricing_rule_args.get("rate"):
                    item.rate = pricing_rule_args.get("rate")

            elif pricing_rule_args.get("free_item_data"):
                apply_pricing_rule_for_free_items(self, pricing_rule_args.get("free_item_data"))

        elif pricing_rule_args.get("validate_applied_rule"):
            for pricing_rule in get_applied_pricing_rules(item.get("pricing_rules")):
                pricing_rule_doc = frappe.get_cached_doc("Pricing Rule", pricing_rule)
                for field in ["discount_percentage", "discount_amount", "rate"]:
                    if item.get(field) < pricing_rule_doc.get(field):
                        title = get_link_to_form("Pricing Rule", pricing_rule)

                        frappe.msgprint(
                            _("Row {0}: user has not applied the rule {1} on the item {2}").format(
                                item.idx, frappe.bold(title), frappe.bold(item.item_code)
                            )
                        )

        item_doc = frappe.get_doc("Item", item.item_code)
        today = datetime.datetime.today().date()
        if item_doc.start_date <= today and item_doc.end_date >= today and item_doc.discount_amount:
            item.rate = item_doc.standard_rate - item_doc.discount_amount
            item.set('rate', item_doc.standard_rate - item_doc.discount_amount)
