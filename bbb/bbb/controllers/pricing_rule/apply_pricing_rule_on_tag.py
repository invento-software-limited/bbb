import frappe
from frappe.utils import flt, today

from erpnext.stock.get_item_details import get_conversion_factor


def get_tag_conditions(values):
    conditions = '''apply_on = "Transaction"'''
    conditions += ''' and `tabPricing Rule`.applicable_for="Tag" '''
    conditions += ''' and disable=0 and "{}" between ifnull(`tabPricing Rule`.valid_from, '2000-01-01')
		and ifnull(`tabPricing Rule`.valid_upto, '2500-12-31')'''.format(today)

    return conditions


def calculate_discount_amount(doc, pricing_rule):
    items = doc.get('items', [])
    total_amount = 0
    discount_amount = 0
    for item in items:
        if item.price_rule_tag == pricing_rule.tag:
            # if item.net_amount:
            # 	total_amount += item.net_amount
            # elif item.price_list_rate and item.discount_amount:
            # 	total_amount += (item.price_list_rate - item.discount_amount) * item.qty
            # elif item.rate:
            # 	total_amount += item.rate * item.qty
            total_amount += item.rate * item.qty

    if pricing_rule.get('discount_percentage'):
        discount_amount = (total_amount * (pricing_rule.get('discount_percentage') / 100))
    elif pricing_rule.get('discount_amount'):
        discount_amount = pricing_rule.get('discount_amount')

    return discount_amount


# Transaction base discount
@frappe.whitelist()
def apply_pricing_rule_on_tag(doc):
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
    print("Pricing Rules On Transaction 1  ====> ", pricing_rules)
    discount_amount = None
    if pricing_rules:
        total_amount = 0
        total_qty = 0
        items = doc.get('items', [])
        for item in items:
            if not item.price_rule_tag:
                continue
            if item.price_rule_tag == pricing_rules[0].get('tag', None):
                total_amount += item.net_amount * item.qty
                total_qty += item.qty

        pricing_rules = filter_pricing_rules_for_qty_amount(total_qty, total_amount, pricing_rules)
        print("Pricing Rules On Transaction 2  ====> ", pricing_rules)

        for d in pricing_rules:
            if d.price_or_product_discount == "Price":

                discount_amount = calculate_discount_amount(doc, d)

                if d.apply_discount_on:
                    doc.set("apply_discount_on", d.apply_discount_on)
                    doc.set("additional_discount_percentage", None)
                    doc.set("discount_amount", flt(discount_amount))
                doc.calculate_taxes_and_totals()
                return True

    if not discount_amount:
        return False
    else:
        return True


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
