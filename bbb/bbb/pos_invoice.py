import frappe
import json
import datetime
import math
from frappe.utils import money_in_words, flt, cint
from frappe import _
from erpnext.accounts.doctype.pricing_rule.utils import filter_pricing_rules_for_qty_amount
from frappe.utils import today, flt, now, cstr, cint
from frappe.defaults import get_defaults
from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.stock_ledger import make_sl_entries
from erpnext.controllers.stock_controller import StockController

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


    if doc.company == 'BBB Restaurant':
        for item in doc.items:
            update_stock_ledger(doc, item)

def on_cancel(doc, method):
    if doc.company == 'BBB Restaurant':
        for item in doc.items:
            update_stock_ledger(doc, item, cancelled=1)

def get_item_list(doc, item):
    item_code = frappe.get_doc('Item', item.item_code)
    warehouse = frappe.db.get_value('POS Profile', doc.pos_profile, 'warehouse')
    if len(item_code.consumable_items) == 0:
        return []

    il = []
    for d in item_code.consumable_items:
        if d.qty is None:
            frappe.throw(_("Row {0}: Qty is mandatory").format(d.idx))
        else:
            il.append(
                frappe._dict(
                    {
                        "warehouse": '',
                        "item_code": d.item_code,
                        "qty": float(d.qty) * float(item.qty),
                        "uom": d.uom,
                        "stock_uom": d.uom,
                        "conversion_factor": 1,
                        "batch_no": cstr(d.get("batch_no")).strip(),
                        "serial_no": cstr(d.get("serial_no")).strip(),
                        "name": d.name,
                        "target_warehouse": warehouse,
                        "company": doc.company,
                        "voucher_type": doc.doctype,
                        "allow_zero_valuation": 0,
                        "consumable_item": d.item_code,
                        "incoming_rate": 0,
                    }
                )
            )

    return il

def update_stock_ledger(doc, item, submitted=0, cancelled=0):
    # self.update_reserved_qty()

    sl_entries = []
    # Loop over items and packed items table
    for d in get_item_list(doc, item):
        # if submitted:
        sl_entries.append(get_sle_for_source_warehouse(doc, d, cancelled = cancelled))
        # elif cancelled:
        #     sl_entries.append(self.get_sle_for_target_warehouse(d, cancelled = cancelled))
    if sl_entries:
        make_sl_entries(sl_entries, allow_negative_stock=True)

def get_sle_for_source_warehouse(doc, item_row, cancelled):
    sle = get_sl_entries(
        doc, item_row,{
                "actual_qty": -1 * flt(item_row.qty),
                "incoming_rate": item_row.incoming_rate,
                "recalculate_rate":cancelled,
                "is_cancelled": cancelled
        },
    )
    return sle

def get_sle_for_target_warehouse(self, item_row, cancelled):
    sle = self.get_sl_entries(
        doc, item_row, {"actual_qty": -1 * flt(item_row.qty), "warehouse": item_row.target_warehouse, 'is_cancelled': cancelled}
    )

    if self.docstatus == 1:
        if not cint(self.is_return):
            sle.update({"incoming_rate": item_row.incoming_rate, "recalculate_rate": 1})
        else:
            sle.update({"outgoing_rate": item_row.incoming_rate})
            if item_row.warehouse:
                sle.dependant_sle_voucher_detail_no = item_row.name

    return sle

def get_sl_entries(doc, d, args):
    valuation_rate = frappe.db.get_value('Item', d.get('item_code'), 'valuation_rate')
    warehouse = frappe.db.get_value('POS Profile', doc.pos_profile, 'warehouse')

    sl_dict = frappe._dict(
        {
            "item_code": d.get("item_code", None),
            "warehouse": warehouse,
            "posting_date": today(),
            "posting_time": frappe.utils.nowtime(),
            "fiscal_year": get_fiscal_year(today(), company=doc.company)[0],
            "voucher_type": doc.doctype,
            "voucher_no": doc.name,
            "voucher_detail_no": d.name,
            # "actual_qty": (self.docstatus == 1 and 1 or -1) * flt(d.get("stock_qty")),
            # "actual_qty": (-1 if self.docstatus == 2 else 1) * flt(d.get("qty")),
            "stock_uom": frappe.db.get_value(
                "Item", args.get("item_code") or d.get("item_code"), "stock_uom"
            ),
            "incoming_rate": 0,
            "valuation_rate": valuation_rate,
            "company": doc.company,
            "batch_no": cstr(d.get("batch_no")).strip(),
            "serial_no": d.get("serial_no"),
            "project": d.get("project", None) or doc.get("project", None),

        }
    )
    sl_dict.update(args)
    return sl_dict
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
        items = doc.items
        restaurant_old_order_list = []
        restaurant_new_order_list = []
        item_str = ""
        old_str = ""
        previous_qty = 0
        for item in items:
            if item.get("type") == "New":
                frappe.msgprint(str("vvvv"))
                str_app = "{item} --- {qty}<br>".format(item=item.get("item_name"),qty=item.get("qty"))
                item_str += str_app
                item.type = "Old"
                previous_qty += item.get("qty")
            else:
                frappe.msgprint(str("ppp"))
                str_app = "{item} --- {qty}<br>".format(item=item.get("item_name"),qty=item.get("qty"))
                old_str += str_app
                previous_qty += item.get("qty")
            
        if len(old_str) > 0:
            all =  old_str + "<hr>" + item_str
        else:
            all = item_str
        if doc.previous_qty != doc.total_qty:
            doc.restaurant_order_item_html = all
        doc.previous_qty = previous_qty

        # for index, item in enumerate(items):
        #     if item.restaurant_new_qty > 0 or (item.restaurant_old_qty > 0 and item.qty > item.restaurant_old_qty and item.restaurant_new_qty == 0):
        #         item.restaurant_new_qty = item.qty - item.restaurant_old_qty
        #     elif restaurant_old_order_list and item.restaurant_old_qty == 0:
        #         item.restaurant_new_qty = item.qty
        #     else:
        #         item.restaurant_old_qty = item.qty
        #         item.restaurant_new_qty = 0

        #     if item.restaurant_new_qty > 0 and item.restaurant_old_qty > 0:
        #         restaurant_old_order_list.append(f'{item.item_name} * {item.restaurant_old_qty}')
        #         restaurant_new_order_list.append(f'{item.item_name} * {item.restaurant_new_qty}')
        #     elif item.restaurant_new_qty > 0:
        #         restaurant_new_order_list.append(f'{item.item_name} * {item.restaurant_new_qty}')
        #     elif item.restaurant_old_qty > 0:
        #         restaurant_old_order_list.append(f'{item.item_name} * {item.restaurant_old_qty}')

        # restaurant_old_order_item_html = '<br>'.join(restaurant_old_order_list)
        # restaurant_new_order_item_html = '<br>'.join(restaurant_new_order_list)
        # if restaurant_new_order_list:
        #     doc.restaurant_order_item_html = restaurant_old_order_item_html + '<hr>' + restaurant_new_order_item_html
        # else:
        #     doc.restaurant_order_item_html = restaurant_old_order_item_html

def restaurant_order_item(doc):
    items_html = ''
    for item in doc.items:
        items_html += (item.item_name + " * " + str(item.qty) + "<br>")
def get_new_order_item(old_item, doc):
    # Create a dictionary to store items from old_item for easy lookup
    old_dict = []
    for item in old_item:
        if item  not in ['<br>', '<hr>']:
            old_split_item = split_item(item)


    # Find the differences
    differences = []
    for item in doc.items:
        new_name, new_value = item.item_name, item.qty

    return differences

# Function to split each item into its name and integer value
def split_item(item):
    # print(item)
    name, value = item.split(' * ')
    return name, int(value)

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
