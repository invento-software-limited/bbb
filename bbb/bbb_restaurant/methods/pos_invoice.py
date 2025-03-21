import frappe
import json
import datetime
import math
from frappe.utils import money_in_words, flt, cint
from frappe import _

from erpnext.accounts.doctype.pricing_rule.utils import filter_pricing_rules_for_qty_amount

class CustomerValidationError(frappe.ValidationError): pass


def after_insert_or_on_submit(doc, method):
    total_advance = doc.total_advance
    grand_total = doc.grand_total
    if grand_total is not None:
        if grand_total < 0:
            rounded_total = math.floor(grand_total)
        else:
            rounded_total = math.ceil(grand_total)
        adjustment = rounded_total - grand_total
        payments = doc.payments

        paid_amount = total_advance
        for payment in payments:
            paid_amount += payment.amount

        change_amount = paid_amount - rounded_total
        # change_amount = (paid_amount - divisible_number) if (paid_amount - divisible_number) > 0 else 0
        outstanding_amount = (rounded_total - paid_amount) if (rounded_total - paid_amount) > 0 else 0
        
        in_words = money_in_words(rounded_total)
        frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
        frappe.db.set_value("POS Invoice", doc.name, "rounded_total", rounded_total)
        frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", rounded_total)

        frappe.db.set_value("POS Invoice", doc.name, "paid_amount", paid_amount - total_advance)
        frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", paid_amount - total_advance)
        frappe.db.set_value("POS Invoice", doc.name, "change_amount", change_amount)
        frappe.db.set_value("POS Invoice", doc.name, "base_change_amount", change_amount)
        frappe.db.set_value("POS Invoice", doc.name, "outstanding_amount", outstanding_amount)
        frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", adjustment)
        frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", adjustment)

    # update product search log
    for item in doc.items:
        search_items = frappe.db.get_all("Product Search Log", filters={"location": doc.pos_profile, "served_by":doc.served_by, "date": doc.posting_date, "product": item.item_code}, fields=["name"], order_by="creation desc")
        if search_items:
            frappe.db.set_value("Product Search Log", search_items[0].get('name'), 'is_sale', 1)

@frappe.whitelist()
def set_pos_cached_data(invoice_data=None):
    invoice_data = json.loads(invoice_data)
    key_list = ['pos_customer', 'pos_served_by', 'pos_ignore_pricing_rule']
    for key, value in invoice_data.items():
        if key == "pos_items":
            item_code = value.get('item_code')
            pos_data = frappe.cache().get_value(frappe.session.user)
            pos_items = pos_data.get('pos_items')
            if pos_items and item_code in pos_items:
                pos_items[item_code]['qty'] = pos_items[item_code]['qty'] + 1
                frappe.cache().set_value(frappe.session.user, pos_data)
            elif pos_items:
                pos_items[item_code] = value
                frappe.cache().set_value(frappe.session.user, pos_data)
            else:
                pos_data['pos_items'] = {item_code: value}
                frappe.cache().set_value(frappe.session.user, pos_data)
        elif key in key_list:
            pos_data = frappe.cache().get_value(frappe.session.user)
            if pos_data:
                pos_data[key] = value
                frappe.cache().set_value(frappe.session.user, pos_data)
            else:
                pos_data = {key: value}
                frappe.cache().set_value(frappe.session.user, pos_data)

            """
    for key, value in invoice_data.items():
        if key == "pos_items":
            item_code = value.get('item_code')
            item_list_of_dict = frappe.cache().get_value(key)
            if item_list_of_dict:
                new_item = True
                for index, item_dict in enumerate(item_list_of_dict):
                    if item_code in item_dict:
                        item_list_of_dict[index][item_code]['qty'] = item_list_of_dict[index][item_code]['qty'] + 1
                        frappe.cache().set_value(key, item_list_of_dict)
                        new_item = not new_item
                        break
                if new_item:
                    item_dict = {item_code: value}
                    item_list_of_dict.append(item_dict)
                    frappe.cache().set_value(key, item_list_of_dict)
            else:
                frappe.cache().set_value(key, [{item_code: value}])
        elif key in key_list:
            frappe.cache().set_value(key, value)
"""


@frappe.whitelist()
def get_pos_cached_data():
    # frappe.cache().delete_value(frappe.session.user)
    pos_data = frappe.cache().get_value(frappe.session.user)
    print('pos_data ', pos_data)
    if pos_data:
        if pos_data.get('pos_customer', None) and pos_data.get('pos_served_by', None):
            data = {}
            pos_item_list = []
            data['pos_customer'] = pos_data.get('pos_customer')
            data['pos_served_by'] = pos_data.get('pos_served_by')
            data['pos_ignore_pricing_rule'] = pos_data.get('pos_ignore_pricing_rule', 0)
            pos_items = pos_data.get('pos_items', {})
            for key, pos_item in pos_items.items():
                pos_item_list.append(pos_item)
            data['pos_items'] = pos_item_list
            return data
        else:
            frappe.cache().delete_value(frappe.session.user)
    else:
        return {}


@frappe.whitelist()
def clear_cached_data():
    frappe.cache().delete_value(frappe.session.user)


@frappe.whitelist()
def remove_single_item_from_cache(item_code=None):
    if (item_code):
        pos_data = frappe.cache().get_value(frappe.session.user)
        pos_items = pos_data.get('pos_items')
        del pos_items[item_code]
        frappe.cache().set_value(frappe.session.user, pos_data)


@frappe.whitelist()
def get_past_order_list(search_term, status, limit=3):
    fields = ["name", "grand_total", "currency", "customer", "posting_time", "posting_date"]
    invoice_list = []

    user = frappe.session.user
    user_roles = frappe.get_roles(user)
    # if user == 'Administrator' or 'Can Return' in user_roles:
    # if user == 'Administrator' in user_roles:
    #     invoices_by_customer = []
    #     invoices_by_name = []
    #     invoices_by_customer_mobile_number = []
    #     if search_term and status:
    #         if status == 'Draft':
    #             invoices_by_customer = frappe.db.get_all(
    #                 "POS Invoice",
    #                 filters={"customer": ["like", "%{}%".format(search_term)], "status": status},
    #                 fields=fields,
    #             )
    #             invoices_by_name = frappe.db.get_all(
    #                 "POS Invoice",
    #                 filters={"name": ["like", "%{}%".format(search_term)], "status": status},
    #                 fields=fields,
    #             )
    #             invoices_by_customer_mobile_number = frappe.db.get_all(
    #                 "POS Invoice",
    #                 filters={"customer_mobile_number": ["like", "%{}%".format(search_term)], "status": status},
    #                 fields=fields,
    #             )
    #
    #         elif status == 'All':
    #             invoices_by_customer = frappe.db.get_all(
    #                 "POS Invoice",
    #                 filters={"customer": ["like", "%{}%".format(search_term)], "status": ["!=", "Draft"]},
    #                 fields=fields,
    #                 limit=3,
    #             )
    #             invoices_by_name = frappe.db.get_all(
    #                 "POS Invoice",
    #                 filters={"name": ["like", "%{}%".format(search_term)], "status": ["!=", "Draft"]},
    #                 fields=fields,
    #                 limit=3,
    #             )
    #             invoices_by_customer_mobile_number = frappe.db.get_all(
    #                 "POS Invoice",
    #                 filters={"customer_mobile_number": ["like", "%{}%".format(search_term)],
    #                          "status": ["!=", "Draft"]},
    #                 fields=fields,
    #                 limit=3,
    #             )
    #         try:
    #             search_term_int = int(search_term)
    #             if len(invoices_by_customer_mobile_number) > 3:
    #                 invoice_list = invoices_by_customer_mobile_number[:3]
    #         except:
    #             if len(invoices_by_name) > 3:
    #                 invoice_list = invoices_by_name[:3]
    #             elif len(invoices_by_name + invoices_by_customer) > 3:
    #                 invoice_list = (invoices_by_name + invoices_by_customer)[:3]
    #             else:
    #                 invoice_list = (invoices_by_name + invoices_by_customer + invoices_by_customer_mobile_number)[:3]
    #
    #     elif status == 'Draft':
    #         invoice_list = frappe.db.get_all("POS Invoice",
    #                                          filters={"status": status},
    #                                          fields=fields)
    #     elif status == 'All':
    #         invoice_list = frappe.db.get_all("POS Invoice",
    #                                          filters={"status": ["!=", "Draft"]},
    #                                          fields=fields, limit=3)
    #     return invoice_list

    if search_term and status:
        if status == 'Draft':
            invoices_by_customer = frappe.db.get_all(
                "POS Invoice",
                filters={"customer": ["like", "%{}%".format(search_term)], "status": status,
                         'owner': frappe.session.user},
                fields=fields,
            )
            invoices_by_name = frappe.db.get_all(
                "POS Invoice",
                filters={"name": ["like", "%{}%".format(search_term)], "status": status, 'owner': frappe.session.user},
                fields=fields,
            )
            invoices_by_customer_mobile_number = frappe.db.get_all(
                "POS Invoice",
                filters={"customer_mobile_number": ["like", "%{}%".format(search_term)], "status": status,
                         'owner': frappe.session.user},
                fields=fields,
            )

            try:
                search_term_int = int(search_term)
                if len(invoices_by_customer_mobile_number) > 3:
                    invoice_list = invoices_by_customer_mobile_number[:3]
            except:
                if len(invoices_by_name) > 3:
                    invoice_list = invoices_by_name[:3]
                elif len(invoices_by_name + invoices_by_customer) > 3:
                    invoice_list = (invoices_by_name + invoices_by_customer)[:3]
                else:
                    invoice_list = (invoices_by_name + invoices_by_customer + invoices_by_customer_mobile_number)[:3]
        elif status == 'All':
            print(search_term)
            invoices_by_name = frappe.db.get_all(
                "POS Invoice",
                filters={"name": search_term, "status": ["!=", "Draft"]},
                fields=fields,
            )
            if invoices_by_name and 'Can Return' in user_roles:
                return invoices_by_name

            invoices_by_customer = frappe.db.get_all(
                "POS Invoice",
                filters={"customer": ["like", "%{}%".format(search_term)], "status": ["!=", "Draft"],
                         'owner': frappe.session.user},
                fields=fields,
                limit=3,
            )
            invoices_by_customer_mobile_number = frappe.db.get_all(
                "POS Invoice",
                filters={"customer_mobile_number": ["like", "%{}%".format(search_term)], "status": ["!=", "Draft"],
                         'owner': frappe.session.user},
                fields=fields,
                limit=3,
            )

            try:
                search_term_int = int(search_term)
                if len(invoices_by_customer_mobile_number) > 3:
                    invoice_list = invoices_by_customer_mobile_number[:3]
                else:
                    invoice_list = invoices_by_customer_mobile_number
                return invoice_list
            except:
                if len(invoices_by_customer) > 3:
                    invoice_list = nvoices_by_customer[:3]
                else:
                    invoice_list = (invoices_by_customer + invoices_by_customer_mobile_number)[:3]
            return invoice_list

        # if len(invoice_list) > 2:
        #     invoice_list = invoice_list[:3]

    elif status == 'Draft':
        invoice_list = frappe.db.get_all("POS Invoice", filters={"status": status, 'owner': frappe.session.user},
                                         fields=fields)
    elif status == 'All':
        invoice_list = frappe.db.get_all("POS Invoice",
                                         filters={"status": ["!=", "Draft"], 'owner': frappe.session.user},
                                         fields=fields, limit=3)
    return invoice_list


def validate(doc, method):
    if not doc.customer:
        frappe.throw(_("You must select a customer before submit"), CustomerValidationError, title="Missing")
    if doc.company == 'BBB Restaurant' and doc.docstatus == 0:
        doc.status = 'Ordered'


def get_tag_conditions(values):
    today = datetime.datetime.today().date()
    conditions = '''apply_on = "Transaction"'''
    conditions += ''' and `tabPricing Rule`.applicable_for="Tag" '''
    conditions += ''' and "{}" between ifnull(`tabPricing Rule`.valid_from, '2000-01-01')
		and ifnull(`tabPricing Rule`.valid_upto, '2500-12-31')'''.format(today)

    return conditions


def calculate_discount_amount(doc, pricing_rule):
    items = doc.get('items', [])
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


# Transaction base discount
@frappe.whitelist()
def apply_pricing_rule_on_tag(doc):
    values = {}
    conditions = get_tag_conditions(values)
    doc = json.loads(doc)
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

        items = doc.get('items', [])
        for item in items:
            if not item.get('price_rule_tag', None):
                continue
            if item.get('price_rule_tag') == pricing_rules[0].get('tag', None):
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
                discount_amount += calculate_discount_amount(doc, d)
                rules_name_list.append(d.title)
                tag_name_list.append(d.tag)
        return {'discount_amount': discount_amount, 'rules_name_list': rules_name_list, 'tag_name_list': tag_name_list}

            # if d.apply_discount_on:
            # 	doc.set("apply_discount_on", d.apply_discount_on)
            # 	doc.set("additional_discount_percentage", None)
            # 	doc.set("discount_amount", flt(discount_amount))
            # for field in ["additional_discount_percentage", "discount_amount"]:
            # 	pr_field = "discount_percentage" if field == "additional_discount_percentage" else field
            #
            #
            #
            # 	if not d.get(pr_field):
            # 		continue
            # 	if (
            # 		d.validate_applied_rule and doc.get(field) is not None and doc.get(field) < d.get(pr_field)
            # 	):
            # 		frappe.msgprint(_("User has not applied rule on the invoice {0}").format(doc.name))
            # 	else:
            # 		if not d.coupon_code_based:
            # 			doc.set(field, d.get(pr_field))
            # 		elif doc.get("coupon_code"):
            # 			# coupon code based pricing rule
            # 			coupon_code_pricing_rule = frappe.db.get_value(
            # 				"Coupon Code", doc.get("coupon_code"), "pricing_rule"
            # 			)
            # 			if coupon_code_pricing_rule == d.name:
            # 				# if selected coupon code is linked with pricing rule
            # 				doc.set(field, d.get(pr_field))
            # 			else:
            # 				# reset discount if not linked
            # 				doc.set(field, 0)
            # 		else:
            # 			# if coupon code based but no coupon code selected
            # 			doc.set(field, 0)

            # doc.calculate_taxes_and_totals()
        # elif d.price_or_product_discount == "Product":
        # 	item_details = frappe._dict({"parenttype": doc.doctype, "free_item_data": []})
        # 	get_product_discount_rule(d, item_details, doc=doc)
        # 	apply_pricing_rule_for_free_items(doc, item_details.free_item_data)
        # 	doc.set_missing_values()
        # 	doc.calculate_taxes_and_totals()


@frappe.whitelist()
def apply_pricing_rule_on_tag_return(doc):
    values = {}
    conditions = get_tag_conditions(values)
    doc = json.loads(doc)
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

        items = doc.get('items', [])
        for item in items:
            if not item.get('price_rule_tag', None):
                continue
            if item.get('price_rule_tag') == pricing_rules[0].get('tag', None):
                total_amount += cint(item.get('rate')) * cint(item.get('qty'))
                total_qty += cint(item.get('qty'))

        pricing_rules = filter_pricing_rules_for_qty_amount(total_qty, total_amount, pricing_rules)
        rules_name_list = []
        tag_name_list = []
        for d in pricing_rules:
            if d.price_or_product_discount == "Price":
                discount_amount += calculate_discount_amount(doc, d)
                rules_name_list.append(d.title)
                tag_name_list.append(d.tag)
        return {'discount_amount': discount_amount, 'rules_name_list': rules_name_list, 'tag_name_list': tag_name_list}
