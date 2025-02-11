import copy
import json
import math

import frappe
from frappe import _, bold
from frappe.utils import cint, flt, fmt_money, get_link_to_form, getdate, today

from erpnext.setup.doctype.item_group.item_group import get_child_item_groups
from erpnext.stock.doctype.warehouse.warehouse import get_child_warehouses
from erpnext.stock.get_item_details import get_conversion_factor


def apply_pricing_rule_on_transaction(doc):
    conditions = "apply_on = 'Transaction'"

    values = {}
    conditions = get_other_conditions(conditions, values, doc)

    pricing_rules = frappe.db.sql(
        f""" Select `tabPricing Rule`.* from `tabPricing Rule`
		where  {conditions} and `tabPricing Rule`.disable = 0
	""",
        values,
        as_dict=1,
    )

    if pricing_rules:
        pricing_rules = filter_pricing_rules_for_qty_amount(doc.total_qty, doc.total, pricing_rules)
        pricing_rules = filter_pricing_rule_based_on_condition(pricing_rules, doc)

        if not pricing_rules:
            remove_free_item(doc)

        for d in pricing_rules:
            if d.price_or_product_discount == "Price":
                if d.apply_discount_on:
                    doc.set("apply_discount_on", d.apply_discount_on)
                # Variable to track whether the condition has been met
                condition_met = False

                for field in ["additional_discount_percentage", "discount_amount"]:
                    pr_field = "discount_percentage" if field == "additional_discount_percentage" else field

                    if not d.get(pr_field):
                        continue

                    if (
                            d.validate_applied_rule
                            and doc.get(field) is not None
                            and doc.get(field) < d.get(pr_field)
                    ):
                        frappe.msgprint(_("User has not applied rule on the invoice {0}").format(doc.name))
                    else:
                        if not d.coupon_code_based:
                            doc.set(field, d.get(pr_field))
                        elif doc.get("coupon_code"):
                            # coupon code based pricing rule
                            coupon_code_pricing_rule = frappe.db.get_value(
                                "Coupon Code", doc.get("coupon_code"), "pricing_rule"
                            )
                            if coupon_code_pricing_rule == d.name:
                                # if selected coupon code is linked with pricing rule
                                doc.set(field, d.get(pr_field))

                                # Set the condition_met variable to True and break out of the loop
                                condition_met = True
                                break

                            else:
                                # reset discount if not linked
                                doc.set(field, 0)
                        else:
                            # if coupon code based but no coupon code selected
                            doc.set(field, 0)

                doc.calculate_taxes_and_totals()

                # Break out of the main loop if the condition is met
                if condition_met:
                    break
            elif d.price_or_product_discount == "Product":
                item_details = frappe._dict({"parenttype": doc.doctype, "free_item_data": []})
                get_product_discount_rule(d, item_details, doc=doc)
                apply_pricing_rule_for_free_items(doc, item_details.free_item_data)
                doc.set_missing_values()
                doc.calculate_taxes_and_totals()


def get_other_conditions(conditions, values, args):
    for field in ["company", "customer", "supplier", "campaign", "sales_partner"]:
        if args.get(field):
            conditions += f" and ifnull(`tabPricing Rule`.{field}, '') in (%({field})s, '')"
            values[field] = args.get(field)
        else:
            conditions += f" and ifnull(`tabPricing Rule`.{field}, '') = ''"

    for parenttype in ["Customer Group", "Territory", "Supplier Group"]:
        group_condition = _get_tree_conditions(args, parenttype, "`tabPricing Rule`")
        if group_condition:
            conditions += " and " + group_condition

    if args.get("transaction_date"):
        conditions += """ and %(transaction_date)s between ifnull(`tabPricing Rule`.valid_from, '2000-01-01')
			and ifnull(`tabPricing Rule`.valid_upto, '2500-12-31')"""
        values["transaction_date"] = args.get("transaction_date")

    if args.get("doctype") in [
        "Quotation",
        "Quotation Item",
        "Sales Order",
        "Sales Order Item",
        "Delivery Note",
        "Delivery Note Item",
        "Sales Invoice",
        "Sales Invoice Item",
        "POS Invoice",
        "POS Invoice Item",
    ]:
        conditions += """ and ifnull(`tabPricing Rule`.selling, 0) = 1"""
    else:
        conditions += """ and ifnull(`tabPricing Rule`.buying, 0) = 1"""

    return conditions


def _get_tree_conditions(args, parenttype, table, allow_blank=True):
    field = frappe.scrub(parenttype)
    condition = ""
    if args.get(field):
        if not frappe.flags.tree_conditions:
            frappe.flags.tree_conditions = {}
        key = (parenttype, args.get(field))
        if key in frappe.flags.tree_conditions:
            return frappe.flags.tree_conditions[key]

        try:
            lft, rgt = frappe.db.get_value(parenttype, args.get(field), ["lft", "rgt"])
        except TypeError:
            frappe.throw(_("Invalid {0}").format(args.get(field)))

        parent_groups = frappe.db.sql_list(
            """select name from `tab{}`
            where lft<={} and rgt>={}""".format(parenttype, "%s", "%s"),
            (lft, rgt),
        )

        if parenttype in ["Customer Group", "Item Group", "Territory"]:
            parent_field = f"parent_{frappe.scrub(parenttype)}"
            root_name = frappe.db.get_list(
                parenttype,
                {"is_group": 1, parent_field: ("is", "not set")},
                "name",
                as_list=1,
                ignore_permissions=True,
            )

            if root_name and root_name[0][0]:
                parent_groups.append(root_name[0][0])

        if parent_groups:
            if allow_blank:
                parent_groups.append("")
            condition = "ifnull({table}.{field}, '') in ({parent_groups})".format(
                table=table, field=field, parent_groups=", ".join(frappe.db.escape(d) for d in parent_groups)
            )

            frappe.flags.tree_conditions[key] = condition
    return condition


def filter_pricing_rules_for_qty_amount(qty, rate, pricing_rules, args=None):
    rules = []

    for rule in pricing_rules:
        status = False
        conversion_factor = 1

        if rule.get("uom"):
            conversion_factor = get_conversion_factor(rule.item_code, rule.uom).get("conversion_factor", 1)

        if flt(qty) >= (flt(rule.min_qty) * conversion_factor) and (
                flt(qty) <= (rule.max_qty * conversion_factor) if rule.max_qty else True
        ):
            status = True

        # if user has created item price against the transaction UOM
        if args and rule.get("uom") == args.get("uom"):
            conversion_factor = 1.0

        if status and (
                flt(rate) >= (flt(rule.min_amt) * conversion_factor)
                and (flt(rate) <= (rule.max_amt * conversion_factor) if rule.max_amt else True)
        ):
            status = True
        else:
            status = False

        if status:
            rules.append(rule)

    return rules


def filter_pricing_rule_based_on_condition(pricing_rules, doc=None):
    filtered_pricing_rules = []
    if doc:
        for pricing_rule in pricing_rules:
            if pricing_rule.condition:
                try:
                    if frappe.safe_eval(pricing_rule.condition, None, doc.as_dict()):
                        filtered_pricing_rules.append(pricing_rule)
                except Exception:
                    pass
            else:
                filtered_pricing_rules.append(pricing_rule)
    else:
        filtered_pricing_rules = pricing_rules

    return filtered_pricing_rules


def get_product_discount_rule(pricing_rule, item_details, args=None, doc=None):
    free_item = pricing_rule.free_item
    if pricing_rule.same_item and pricing_rule.get("apply_on") != "Transaction":
        free_item = item_details.item_code or args.item_code

    if not free_item:
        frappe.throw(
            _("Free item not set in the pricing rule {0}").format(
                get_link_to_form("Pricing Rule", pricing_rule.name)
            )
        )

    qty = pricing_rule.free_qty or 1
    if pricing_rule.is_recursive:
        transaction_qty = sum(
            [
                row.qty
                for row in doc.items
                if not row.is_free_item
                   and row.item_code == args.item_code
                   and row.pricing_rules == args.pricing_rules
            ]
        )
        transaction_qty = transaction_qty - pricing_rule.apply_recursion_over
        if transaction_qty and transaction_qty > 0:
            qty = flt(transaction_qty) * qty / pricing_rule.recurse_for
            if pricing_rule.round_free_qty:
                qty = (flt(transaction_qty) // pricing_rule.recurse_for) * (pricing_rule.free_qty or 1)

    if not qty:
        return

    free_item_data_args = {
        "item_code": free_item,
        "qty": qty,
        "pricing_rules": pricing_rule.name,
        "rate": pricing_rule.free_item_rate or 0,
        "price_list_rate": pricing_rule.free_item_rate or 0,
        "is_free_item": 1,
    }

    item_data = frappe.get_cached_value(
        "Item", free_item, ["item_name", "description", "stock_uom"], as_dict=1
    )

    free_item_data_args.update(item_data)
    free_item_data_args["uom"] = pricing_rule.free_item_uom or item_data.stock_uom
    free_item_data_args["conversion_factor"] = get_conversion_factor(
        free_item, free_item_data_args["uom"]
    ).get("conversion_factor", 1)

    if item_details.get("parenttype") == "Purchase Order":
        free_item_data_args["schedule_date"] = doc.schedule_date if doc else today()

    if item_details.get("parenttype") == "Sales Order":
        free_item_data_args["delivery_date"] = doc.delivery_date if doc else today()

    item_details.free_item_data.append(free_item_data_args)


def remove_free_item(doc):
    for d in doc.items:
        if d.is_free_item:
            doc.remove(d)


def apply_pricing_rule_for_free_items(doc, pricing_rule_args):
    if pricing_rule_args:
        args = {(d["item_code"], d["pricing_rules"]): d for d in pricing_rule_args}

        for item in doc.items:
            if not item.is_free_item:
                continue

            free_item_data = args.get((item.item_code, item.pricing_rules))
            if free_item_data:
                free_item_data.pop("item_name")
                free_item_data.pop("description")
                item.update(free_item_data)
                args.pop((item.item_code, item.pricing_rules))

        for free_item in args.values():
            doc.append("items", free_item)
