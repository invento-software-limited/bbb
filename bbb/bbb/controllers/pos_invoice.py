# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt


import frappe
import datetime
import math

import requests
from frappe import _
from frappe.utils import cint, flt, get_link_to_form, getdate, nowdate

from bbb.bbb.controllers.pricing_rule.utils import (
    apply_pricing_rule_for_free_items,
    apply_pricing_rule_on_transaction,
    get_applied_pricing_rules,
)

from bbb.bbb.controllers.erp_doctype.pos_invoice import POSInvoice
from erpnext.stock.doctype.serial_no.serial_no import get_pos_reserved_serial_nos, get_serial_nos

from bbb.bbb.controllers.get_item_details import (
	_get_item_tax_template,
	get_conversion_factor,
	get_item_details,
	get_item_tax_map,
	get_item_warehouse,
)

from erpnext.accounts.doctype.pricing_rule.utils import filter_pricing_rules_for_qty_amount

from bbb.bbb.pos_invoice import get_tag_conditions, calculate_discount_amount

force_item_fields = (
	"item_group",
	"brand",
	"stock_uom",
	"is_fixed_asset",
	"pricing_rules",
	"weight_per_unit",
	"weight_uom",
	"total_weight",
	"valuation_rate",
)

class CustomPOSInvoice(POSInvoice):
    def __init__(self, *args, **kwargs):
        super(CustomPOSInvoice, self).__init__(*args, **kwargs)

    def validate(self):
    # run on validate method of selling controller
        super(CustomPOSInvoice, self).validate()

    # self.validate_pos_return()
    # munim fine
    # validate amount in mode of payments for returned invoices for pos must be negative
    # if self.is_pos and self.is_return:
    #     self.verify_payment_amount_is_negative()

    # def apply_pricing_rule_on_items(self, item, pricing_rule_args):
    #     print(pricing_rule_args)
    #     if not pricing_rule_args.get("validate_applied_rule", 0):
    #         # if user changed the discount percentage then set user's discount percentage ?
    #         if pricing_rule_args.get("price_or_product_discount") == "Price":
    #             item.set("pricing_rules", pricing_rule_args.get("pricing_rules"))
    #             item.set("discount_percentage", pricing_rule_args.get("discount_percentage"))
    #             item.set("discount_amount", pricing_rule_args.get("discount_amount"))
    #             if pricing_rule_args.get("pricing_rule_for") == "Rate":
    #                 item.set("price_list_rate", pricing_rule_args.get("price_list_rate"))
    #
    #             if item.get("price_list_rate"):
    #                 item.rate = flt(
    #                     item.price_list_rate * (1.0 - (flt(item.discount_percentage) / 100.0)),
    #                     item.precision("rate"),
    #                 )
    #
    #                 if item.get("discount_amount"):
    #                     item.rate = item.price_list_rate - item.discount_amount
    #
    #             if item.get("apply_discount_on_discounted_rate") and pricing_rule_args.get("rate"):
    #                 item.rate = pricing_rule_args.get("rate")
    #
    #         elif pricing_rule_args.get("free_item_data"):
    #             apply_pricing_rule_for_free_items(self, pricing_rule_args.get("free_item_data"))
    #
    #     elif pricing_rule_args.get("validate_applied_rule"):
    #         for pricing_rule in get_applied_pricing_rules(item.get("pricing_rules")):
    #             pricing_rule_doc = frappe.get_cached_doc("Pricing Rule", pricing_rule)
    #             for field in ["discount_percentage", "discount_amount", "rate"]:
    #                 if item.get(field) < pricing_rule_doc.get(field):
    #                     title = get_link_to_form("Pricing Rule", pricing_rule)
    #
    #                     frappe.msgprint(
    #                         _("Row {0}: user has not applied the rule {1} on the item {2}").format(
    #                             item.idx, frappe.bold(title), frappe.bold(item.item_code)
    #                         )
    #                     )
    #
    #     # item_doc = frappe.get_doc("Item", item.item_code)
    #     # today = datetime.datetime.today().date()
    #     # if item_doc.start_date and item_doc.end_date and item_doc.discount_amount and item_doc.start_date <= today and item_doc.end_date >= today:
    #     #     item.rate = item_doc.standard_rate - item_doc.discount_amount
    #     #     item.set('rate', item_doc.standard_rate - item_doc.discount_amount)





    def validate_qty(self):
        """Validates qty at row level"""
        self.item_allowance = {}
        self.global_qty_allowance = None
        self.global_amount_allowance = None

        for args in self.status_updater:
            if "target_ref_field" not in args:
                # if target_ref_field is not specified, the programmer does not want to validate qty / amount
                continue

            # get unique transactions to update
            for d in self.get_all_children():
                if hasattr(d, 'qty') and d.qty < 0 and not self.get('is_return'):
                    frappe.throw(_("For an item {0}, quantity must be positive number").format(d.item_code))
                # munim fine
                # if hasattr(d, 'qty') and d.qty > 0 and self.get('is_return'):
                # 	frappe.throw(_("For an item {0}, quantity must be negative number").format(d.item_code))

                if d.doctype == args['source_dt'] and d.get(args["join_field"]):
                    args['name'] = d.get(args['join_field'])

                    # get all qty where qty > target_field
                    item = frappe.db.sql("""select item_code, `{target_ref_field}`,
                        `{target_field}`, parenttype, parent from `tab{target_dt}`
                        where `{target_ref_field}` < `{target_field}`
                        and name=%s and docstatus=1""".format(**args),
                                         args['name'], as_dict=1)
                    if item:
                        item = item[0]
                        item['idx'] = d.idx
                        item['target_ref_field'] = args['target_ref_field'].replace('_', ' ')

                        # if not item[args['target_ref_field']]:
                        # 	msgprint(_("Note: System will not check over-delivery and over-booking for Item {0} as quantity or amount is 0").format(item.item_code))
                        if args.get('no_allowance'):
                            item['reduce_by'] = item[args['target_field']] - item[args['target_ref_field']]
                            if item['reduce_by'] > .01:
                                self.limits_crossed_error(args, item, "qty")

                        elif item[args['target_ref_field']]:
                            self.check_overflow_with_allowance(item, args)

    def validate_return_items_qty(self):
        if not self.get("is_return"): return

        for d in self.get("items"):
            # munim fine
            # if d.get("qty") > 0:
            # 	frappe.throw(
            # 		_("Row #{}: You cannot add postive quantities in a return invoice. Please remove item {} to complete the return.")
            # 		.format(d.idx, frappe.bold(d.item_code)), title=_("Invalid Item")
            # 	)
            if d.get("serial_no"):
                serial_nos = get_serial_nos(d.serial_no)
                for sr in serial_nos:
                    serial_no_exists = frappe.db.sql("""
    					SELECT name
    					FROM `tabPOS Invoice Item`
    					WHERE
    						parent = %s
    						and (serial_no = %s
    							or serial_no like %s
    							or serial_no like %s
    							or serial_no like %s
    						)
    				""", (self.return_against, sr, sr + '\n%', '%\n' + sr, '%\n' + sr + '\n%'))

                    if not serial_no_exists:
                        bold_return_against = frappe.bold(self.return_against)
                        bold_serial_no = frappe.bold(sr)
                        frappe.throw(
                            _("Row #{}: Serial No {} cannot be returned since it was not transacted in original invoice {}")
                            .format(d.idx, bold_serial_no, bold_return_against)
                        )

    def validate_payment_amount(self):
        total_amount_in_payments = 0
        for entry in self.payments:
            total_amount_in_payments += entry.amount
            if not self.is_return and entry.amount < 0:
                frappe.throw(_("Row #{0} (Payment Table): Amount must be positive").format(entry.idx))
            # munim fine need to add permission here
        user = frappe.session.user
        user_roles = frappe.get_roles(user)
        if user == 'Administrator' or 'Can Return' in user_roles:
            pass
        elif self.is_return and entry.amount > 0:
            frappe.throw(_("Row #{0} (Payment Table): Amount must be negative").format(entry.idx))

        if self.is_return:
            invoice_total = self.rounded()
            if total_amount_in_payments and total_amount_in_payments < invoice_total:
                frappe.throw(_("Total payments amount can't be greater than {}").format(-invoice_total))

    def validate_pos(self):
        if self.is_return:
            invoice_total = self.rounded()

            # if flt(self.paid_amount) + flt(self.write_off_amount) - flt(invoice_total) > 1.0 / (
            #         10.0 ** (self.precision("grand_total") + 1.0)
            # ):
            #     frappe.throw(_("Paid amount + Write Off Amount can not be greater than Grand Total"))

    def verify_payment_amount_is_negative(self):
        # for entry in self.payments:
        #     if entry.amount > 0:
        #         frappe.throw(_("Row #{0} (Payment Table): Amount must be negative").format(entry.idx))
        pass

    def validate_pos_return(self):
        if self.is_consolidated:
            # pos return is already validated in pos invoice
            return

        if self.is_pos and self.is_return:
            total_amount_in_payments = 0
            for payment in self.payments:
                total_amount_in_payments += payment.amount
            invoice_total = self.rounded()
            if total_amount_in_payments < invoice_total:
                frappe.throw(_("Total payments amount can't be greater than {}").format(-invoice_total))

    def rounded(self):
        invoice_total = self.grand_total
        if invoice_total < 0:
            return math.floor(invoice_total)
        else:
            return math.ceil(invoice_total)
        # five_basis_total = int(invoice_total / 5) * 5
        # adjustment = flt(abs(invoice_total - five_basis_total), 2)
        # if five_basis_total < 0:
        #     if (adjustment > 2.49):
        #         return five_basis_total - 5
        #     else:
        #         return five_basis_total
        # else:
        #     if (adjustment > 2.49):
        #         return five_basis_total + 5
        #     else:
        #         return five_basis_total

    def set_status(self, update=False, status=None, update_modified=True):
        rounded_total = self.rounded()
        paid_amount = self.paid_amount
        outstanding_amount = (rounded_total - self.total_advance) - paid_amount

        if self.is_new():
            if self.get("amended_from"):
                self.status = "Draft"
            return

        if not status:
            if self.docstatus == 2:
                status = "Cancelled"
            elif self.docstatus == 1:
                if self.consolidated_invoice:
                    self.status = "Consolidated"
                elif (
                        flt(outstanding_amount) > 0
                        and getdate(self.due_date) < getdate(nowdate())
                        and self.is_discounted
                        and self.get_discounting_status() == "Disbursed"
                ):
                    self.status = "Overdue and Discounted"
                elif flt(outstanding_amount) > 0 and getdate(self.due_date) < getdate(nowdate()):
                    self.status = "Overdue"
                elif (
                        flt(outstanding_amount) > 0
                        and getdate(self.due_date) >= getdate(nowdate())
                        and self.is_discounted
                        and self.get_discounting_status() == "Disbursed"
                ):
                    self.status = "Unpaid and Discounted"
                elif flt(outstanding_amount) > 0 and getdate(self.due_date) >= getdate(nowdate()):
                    self.status = "Unpaid"
                elif (
                        flt(outstanding_amount) <= 0
                        and self.is_return == 0
                        and frappe.db.get_value(
                    "POS Invoice", {"is_return": 1, "return_against": self.name, "docstatus": 1}
                )
                ):
                    self.status = "Credit Note Issued"
                elif self.is_return == 1:
                    self.status = "Return"
                elif flt(outstanding_amount) <= 0:
                    self.status = "Paid"
                else:
                    self.status = "Submitted"
            else:
                self.status = "Draft"

        if update:
            self.db_set("status", self.status, update_modified=update_modified)

    @frappe.whitelist()
    def set_advance_booking_advances(self):
        """Returns list of advances against Account, Party, Reference"""
        advance_booking_doc = frappe.get_doc(
            'Advance Booking', self.advance_booking_doc)
        
        self.set("advances", [])
        advance_allocated = 0
        # if self.get("party_account_currency") == self.company_currency:
        # 	amount = self.get("base_rounded_total") or self.base_grand_total
        # else:
        # 	amount = self.get("rounded_total") or self.grand_total

        # allocated_amount = min(self.rounded_total - advance_allocated, advance_booking_doc.total_advance)
        # advance_allocated += flt(allocated_amount)
        outstanding_amount = self.rounded_total - advance_booking_doc.total_advance

        advance_row = frappe._dict({
            "parent": self.name,
            "parenttype": "Sales Invoice",
            "doctype": "Sales Invoice Advance",
            "reference_type": "Advance Booking",
            "reference_name": advance_booking_doc.name,
            "remarks": 'Amount BDT {} received from {}'.format(advance_booking_doc.total_advance, advance_booking_doc.customer),
            "advance_amount": flt(advance_booking_doc.total_advance),
            "allocated_amount": flt(advance_booking_doc.total_advance),
            "ref_exchange_rate": 1
        })

        # self.paid_amount = flt(self.rounded_total - advance_booking_doc.total_advance)
        self.set("outstanding_amount", 0)
        self.set("advances", [advance_row])

    def set_missing_item_details(self, for_validate=False):
        """set missing item values"""
        from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

        if hasattr(self, "items"):
            parent_dict = {}
            for fieldname in self.meta.get_valid_columns():
                parent_dict[fieldname] = self.get(fieldname)

            if self.doctype in ["Quotation", "Sales Order", "Delivery Note", "Sales Invoice"]:
                document_type = f"{self.doctype} Item"
                parent_dict.update({"document_type": document_type})

            # party_name field used for customer in quotation
            if (
                    self.doctype == "Quotation"
                    and self.quotation_to == "Customer"
                    and parent_dict.get("party_name")
            ):
                parent_dict.update({"customer": parent_dict.get("party_name")})

            self.pricing_rules = []

            for item in self.get("items"):
                if item.get("item_code"):
                    args = parent_dict.copy()
                    args.update(item.as_dict())

                    args["doctype"] = self.doctype
                    args["name"] = self.name
                    args["child_doctype"] = item.doctype
                    args["child_docname"] = item.name
                    args["ignore_pricing_rule"] = (
                        self.ignore_pricing_rule if hasattr(self, "ignore_pricing_rule") else 0
                    )

                    if not args.get("transaction_date"):
                        args["transaction_date"] = args.get("posting_date")

                    if self.get("is_subcontracted"):
                        args["is_subcontracted"] = self.is_subcontracted

                    ret = get_item_details(args, self, for_validate=for_validate, overwrite_warehouse=False)
                    for fieldname, value in ret.items():
                        if item.meta.get_field(fieldname) and value is not None:
                            if (
                                    item.get(fieldname) is None
                                    or fieldname in force_item_fields
                                    or (
                                    fieldname in ["serial_no", "batch_no"]
                                    and item.get("use_serial_batch_fields")
                            )
                            ):
                                item.set(fieldname, value)

                            elif fieldname in ["cost_center", "conversion_factor"] and not item.get(
                                    fieldname
                            ):
                                item.set(fieldname, value)
                            elif fieldname == "item_tax_rate" and not (
                                    self.get("is_return") and self.get("return_against")
                            ):
                                item.set(fieldname, value)
                            elif fieldname == "serial_no":
                                # Ensure that serial numbers are matched against Stock UOM
                                item_conversion_factor = item.get("conversion_factor") or 1.0
                                item_qty = abs(item.get("qty")) * item_conversion_factor

                                if item_qty != len(get_serial_nos(item.get("serial_no"))):
                                    item.set(fieldname, value)

                            elif (
                                    ret.get("pricing_rule_removed")
                                    and value is not None
                                    and fieldname
                                    in [
                                        "discount_percentage",
                                        "discount_amount",
                                        "rate",
                                        "margin_rate_or_amount",
                                        "margin_type",
                                        "remove_free_item",
                                    ]
                            ):
                                # reset pricing rule fields if pricing_rule_removed
                                item.set(fieldname, value)

                    if self.doctype in ["Purchase Invoice", "Sales Invoice"] and item.meta.get_field(
                            "is_fixed_asset"
                    ):
                        item.set("is_fixed_asset", ret.get("is_fixed_asset", 0))

                    # Double check for cost center
                    # Items add via promotional scheme may not have cost center set
                    if hasattr(item, "cost_center") and not item.get("cost_center"):
                        item.set(
                            "cost_center",
                            self.get("cost_center") or erpnext.get_default_cost_center(self.company),
                        )

                    if ret.get("pricing_rules"):
                        self.apply_pricing_rule_on_items(item, ret)
                        self.set_pricing_rule_details(item, ret)
                else:
                    # Transactions line item without item code

                    uom = item.get("uom")
                    stock_uom = item.get("stock_uom")
                    if bool(uom) != bool(stock_uom):  # xor
                        item.stock_uom = item.uom = uom or stock_uom

                    # UOM cannot be zero so substitute as 1
                    item.conversion_factor = (
                            get_uom_conv_factor(item.get("uom"), item.get("stock_uom"))
                            or item.get("conversion_factor")
                            or 1
                    )

            if self.doctype == "Purchase Invoice":
                self.set_expense_account(for_validate)


    def validate_apply_pricing_rule_on_tag(self):
        values = {}
        conditions = get_tag_conditions(values)
        pricing_rules = frappe.db.sql(
            """ Select `tabPricing Rule`.* from `tabPricing Rule`
            where  {conditions} and `tabPricing Rule`.disable = 0 order by `tabPricing Rule`.priority desc
        """.format(
                conditions=conditions
            ),
            values,
            as_dict=1,
        )
        if pricing_rules:
            total_amount = 0
            total_qty = 0
            discount_amount = 0

            items = self.items
            for item in items:
                if not item.price_rule_tag:
                    continue
                if item.price_rule_tag == pricing_rules[0].get('tag', None):
                    if cint(item.get('qty')) < 0:
                        qty = (-1) * cint(item.get('qty'))
                    else:
                        qty = cint(item.get('qty'))

                    total_amount += cint(item.get('rate')) * cint(qty)
                    total_qty += cint(qty)

            pricing_rules = filter_pricing_rules_for_qty_amount(total_qty, total_amount, pricing_rules)
            rules_name_list = []
            tag_name_list = []
            for d in pricing_rules:
                if d.price_or_product_discount == "Price":
                    discount_amount += self.calculate_applied_tag_discount_amount(d)
                    rules_name_list.append(d.title)
                    tag_name_list.append(d.tag)
            return discount_amount, rules_name_list, tag_name_list

    def calculate_applied_tag_discount_amount(self, pricing_rule):
        items = self.items
        total_amount = 0
        discount_amount = 0
        for item in items:
            if item.get('price_rule_tag') == pricing_rule.tag:
                total_amount += cint(item.get('rate')) * cint(item.get('qty'))

        if pricing_rule.get('discount_percentage'):
            discount_amount = (total_amount * (pricing_rule.get('discount_percentage') / 100))
        elif pricing_rule.get('discount_amount'):
            discount_amount = pricing_rule.get('discount_amount')

        return discount_amount

    def update_special_discount_amount(self):
        discount_amount, rules_name_list, tag_name_list = self.validate_apply_pricing_rule_on_tag()
        tag_name = ','.join(tag_name_list)
        rules_name = ','.join(rules_name_list)
        self.additional_discount_tag_name = tag_name
        self.additional_discount_pricing_rule_name = rules_name
        self.discount_amount = discount_amount
        self.calculate_taxes_and_totals()