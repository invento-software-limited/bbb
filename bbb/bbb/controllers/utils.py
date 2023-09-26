import json

import frappe
import datetime
from frappe.permissions import get_doctypes_with_read
from frappe.utils import cint, cstr, now
from frappe.utils import cint, flt, fmt_money, get_link_to_form, getdate, today, cstr
from frappe.model.naming import set_name_from_naming_options

from erpnext.accounts.doctype.pricing_rule.utils import filter_pricing_rules_for_qty_amount


def cint(s, default=0):
    """Convert to integer

        :param s: Number in string or other numeric format.
        :returns: Converted number in python integer type.

        Returns default if input can not be converted to integer.

        Examples:
        >>> cint("100")
        100
        >>> cint("a")
        0

    """
    try:
        return int(float(s))
    except Exception:
        return default


def rounded(num, precision=0):
    """round method for round halfs to nearest even algorithm aka banker's rounding - compatible with python3"""
    precision = cint(precision)
    multiplier = 10 ** precision

    # avoid rounding errors
    num = round(num * multiplier if precision else num, 8)

    floor_num = math.floor(num)
    decimal_part = num - floor_num

    if not precision and decimal_part == 0.5:
        num = floor_num if (floor_num % 2 == 0) else floor_num + 1
    else:
        if decimal_part == 0.5:
            num = floor_num + 1
        else:
            num = round(num)

    return (num / multiplier) if precision else num


@frappe.whitelist()
def pos_invoice_rounded_total(num=None):
    # rounding : M rounds to 5 basis ( 12.49 will be 10 and 12.5 will  be 15)
    if num is None:
        data = {
            'rounded_total': 0,
            'rounded_adjustment': 0
        }
        return data
    float_number = float(num)
    int_number = int(float_number)
    divisible_number = (int_number // 5) * 5
    adjustment = float_number - divisible_number
    rounding_total = 0
    rounded_adjustment = 0
    if adjustment < 2.50:
        rounding_total = divisible_number
        rounded_adjustment = -(adjustment)
    elif adjustment > 2.49:
        rounding_total = divisible_number + 5
        rounded_adjustment = rounding_total - float_number
    data = {
        'rounded_total': rounding_total,
        'rounding_adjustment': "%.2f" % rounded_adjustment
    }
    return data


def scrub_options_list(ol):
    options = list(filter(lambda x: x, [cstr(n).strip() for n in ol]))
    return options


@frappe.whitelist()
def set_series_for(doctype="POS Profile"):
    doc = frappe.get_doc('Naming Series')
    ol = doc.set_options.split("\n")
    options = scrub_options_list(ol)

    if options and doc.user_must_always_select:
        options = [''] + options

    default = options[0] if options else ''

    # update in property setter
    prop_dict = {'options': "\n".join(options), 'default': default}

    for prop in prop_dict:
        ps_exists = frappe.db.get_value("Property Setter",
                                        {"field_name": '_naming_series', 'doc_type': doctype, 'property': prop})
        print(ps_exists)

        if ps_exists:
            ps = frappe.get_doc('Property Setter', ps_exists)
            ps.value = prop_dict[prop]
            ps.save()
        else:
            ps = frappe.get_doc({
                'doctype': 'Property Setter',
                'doctype_or_field': 'DocField',
                'doc_type': doctype,
                'field_name': '_naming_series',
                'property': prop,
                'value': prop_dict[prop],
                'property_type': 'Text',
                '__islocal': 1
            })
            ps.save()

    # self.set_options = "\n".join(options)

    frappe.clear_cache(doctype=doctype)
    return True


@frappe.whitelist()
def get_naming_series(doctype=None):
    if doctype is None:
        return []
    doc = frappe.get_doc('Naming Series')
    try:
        options = doc.get_options(doctype)
        option_list = options.split('\n')
        return option_list

    except frappe.DoesNotExistError:
        return []


def get_default_naming_series(doctype):
    """get default value for `naming_series` property"""
    naming_series = frappe.get_meta(doctype).get_field("naming_series").options or ""
    if naming_series:
        naming_series = naming_series.split("\n")
        return naming_series[0] or naming_series[1]
    else:
        return None


@frappe.whitelist()
def str_to_datetime(posting_date, posting_time):
    p_datetime = posting_date + " " + posting_time
    posting_datetime = datetime.datetime.strptime(p_datetime, '%d-%m-%Y %H:%M:%S')
    datetime_format = datetime.datetime.strftime(posting_datetime, '%Y-%m-%d %I:%M %p')
    return datetime_format


@frappe.whitelist()
def get_current_datetime():
    now = datetime.datetime.now()
    current_datetime = datetime.datetime.strftime(now, '%Y-%m-%d %I:%M %p')
    return current_datetime


@frappe.whitelist()
def get_item_discount_amount(qty, discount_rate):
    discount_amount = float(qty) * float(discount_rate)
    return discount_amount


@frappe.whitelist()
def get_invoice_total_discount_amount(doctype, docname):
    invoice = frappe.get_doc(doctype, docname)
    items = invoice.items
    item_total_discount = 0
    for item in items:
        mrp_amount = float(item.qty) * float(item.price_list_rate)
        total_amount = float(item.qty) * float(item.rate)
        item_total_discount += (mrp_amount - total_amount)

    total_discount = item_total_discount + invoice.discount_amount
    return total_discount


@frappe.whitelist()
def get_item_total_discount_amount(doctype, docname):
    invoice = frappe.get_doc(doctype, docname)
    items = invoice.items
    item_total_discount = 0

    for item in items:
        qty = -1 * item.qty if item.qty < 0 else item.qty
        mrp_amount = float(qty) * float(item.price_list_rate)
        total_amount = float(qty) * float(item.rate)
        discount = (mrp_amount - total_amount)
        item_total_discount += (discount - item.total_damaged_cost)
    return item_total_discount


@frappe.whitelist()
def get_invoice_before_discount_amount(doctype, docname):
    invoice = frappe.get_doc(doctype, docname)
    items = invoice.items
    total_mrp_amount = 0
    for item in items:
        mrp_amount = float(item.qty) * float(item.price_list_rate)
        total_mrp_amount += mrp_amount
    return total_mrp_amount


@frappe.whitelist()
def get_pricing_rule_discount(name):
    docname_list = json.loads(name)
    try:
        pricing_rule_doc = frappe.get_doc('Pricing Rule', {'name': docname_list[0], "disable": 0})
        if pricing_rule_doc:
            data = {'discount_percentage': pricing_rule_doc.discount_percentage,
                    'discount_amount': pricing_rule_doc.discount_amount}
            return data
        else:
            data = {'discount_percentage': 0, 'discount_amount': 0}
            return data
    except:
        pass


@frappe.whitelist()
def get_and_apply_item_pricing_rules(return_against):
    return_against_doc = frappe.get_doc('POS Invoice', {'name': return_against})
    return return_against_doc.pricing_rules


@frappe.whitelist()
def apply_item_pricing_rule(return_against, item_code):
    return_against_doc = frappe.get_doc('POS Invoice', {'name': return_against})
    margin_type = ''
    discount_percentage = 0
    discount_amount = 0
    for pricing_rule in return_against_doc.pricing_rules:
        if pricing_rule.item_code == item_code:
            pricing_rule_doc = frappe.get_doc('Pricing Rule', {'name': pricing_rule.pricing_rule})
            # print(pricing_rule_doc.__dict__)
            margin_type = pricing_rule_doc.margin_type
            discount_percentage = pricing_rule_doc.discount_percentage
            discount_amount = pricing_rule_doc.discount_amount
    return {'margin_type': margin_type, 'discount_amount': discount_amount, 'discount_percentage': discount_percentage}


@frappe.whitelist()
def apply_all_items_pricing_rules(return_against):
    return_against_doc = frappe.get_doc('POS Invoice', {'name': return_against})
    # pricing_rule_data_dict = dict()

    # for pricing_rule in return_against_doc.pricing_rules:
    #     pricing_rule_doc = frappe.get_doc('Pricing Rule', {'name': pricing_rule.pricing_rule})
    #     margin_type = pricing_rule_doc.margin_type
    #     discount_percentage = pricing_rule_doc.discount_percentage
    #     discount_amount = pricing_rule_doc.discount_amount
    #     pricing_rule_data_dict[pricing_rule.item_code] = {'margin_type': margin_type,
    #                                                       'discount_amount': discount_amount,
    #                                                       'discount_percentage': discount_percentage
    #                                                       }

    item_wise_discount_percentage = []
    for index, item in enumerate(return_against_doc.items):
        item_wise_discount_percentage.append({'margin_type': item.margin_type,
                                              'discount_amount': item.discount_amount,
                                              'discount_percentage': item.discount_percentage,
                                              'rate': item.rate,
                                              'item_code': str(index) + "_" + item.item_code,
                                              })
    return item_wise_discount_percentage


@frappe.whitelist()
def get_item_rate_discount(return_against, item_code):
    return_against_doc = frappe.get_doc('POS Invoice', {'name': return_against})

    for index, item in enumerate(return_against_doc.items):
        if item.item_code == item_code and item.discount_percentage < 100:
            return {'discount_amount': item.discount_amount, 'discount_percentage': item.discount_percentage,
                    'rate': item.rate, }


# def get_tag_conditions(values):
#     conditions = '''apply_on = "Transaction"'''
#     conditions += ''' and `tabPricing Rule`.applicable_for="Tag" '''
#     conditions += ''' and "{}" between ifnull(`tabPricing Rule`.valid_from, '2000-01-01')
# 		and ifnull(`tabPricing Rule`.valid_upto, '2500-12-31')'''.format(today)
#
#     return conditions
#
#
# def calculate_discount_amount(doc, pricing_rule):
#     items = doc.get('items', [])
#     total_amount = 0
#     discount_amount = 0
#     for item in items:
#         if item.price_rule_tag == pricing_rule.tag:
#             # if item.net_amount:
#             # 	total_amount += item.net_amount
#             # elif item.price_list_rate and item.discount_amount:
#             # 	total_amount += (item.price_list_rate - item.discount_amount) * item.qty
#             # elif item.rate:
#             # 	total_amount += item.rate * item.qty
#             total_amount += item.rate * item.qty
#
#     if pricing_rule.get('discount_percentage'):
#         discount_amount = (total_amount * (pricing_rule.get('discount_percentage') / 100))
#     elif pricing_rule.get('discount_amount'):
#         discount_amount = pricing_rule.get('discount_amount')
#
#     return discount_amount
#
#
# # Transaction base discount
# @frappe.whitelist()
# def apply_pricing_rule_on_tag(doc):
#     values = {}
#     conditions = get_tag_conditions(values)
#     pricing_rules = frappe.db.sql(
#         """ Select `tabPricing Rule`.* from `tabPricing Rule`
#         where  {conditions} and `tabPricing Rule`.disable = 0 order by `tabPricing Rule`.priority desc
#     """.format(
#             conditions=conditions
#         ),
#         values,
#         as_dict=1,
#     )
#     discount_amount = None
#     if pricing_rules:
#         total_amount = 0
#         total_qty = 0
#         items = doc.get('items', [])
#         for item in items:
#             if not item.price_rule_tag:
#                 continue
#             if item.price_rule_tag == pricing_rules[0].get('tag', None):
#                 total_amount += item.net_amount * item.qty
#                 total_qty += item.qty
#
#         pricing_rules = filter_pricing_rules_for_qty_amount(total_qty, total_amount, pricing_rules)
#
#         for d in pricing_rules:
#             if d.price_or_product_discount == "Price":
#
#                 discount_amount = calculate_discount_amount(doc, d)
#
#                 if d.apply_discount_on:
#                     doc.set("apply_discount_on", d.apply_discount_on)
#                     doc.set("additional_discount_percentage", None)
#                     doc.set("discount_amount", flt(discount_amount))
#                 doc.calculate_taxes_and_totals()
#                 return True
#
#     if not discount_amount:
#         return False
#     else:
#         return True


@frappe.whitelist()
def resolved_accounts_receivable():
    sales_invoices = get_accounts_receivable_invoices()
    invoice_list = []
    i = 0
    for invoice in sales_invoices:
        sales_invoice = frappe.get_doc('Sales Invoice', invoice.get('name'))
        invoice_list.append(sales_invoice.name)
        if sales_invoice.rounded_total > 0 and sales_invoice.paid_amount > sales_invoice.rounded_total:
            outstanding_amount = sales_invoice.outstanding_amount
            if outstanding_amount < 0:
                change_amount_abs = abs(0 - outstanding_amount)
                posting_date = sales_invoice.posting_date
                year = posting_date.year
                # print(year, change_amount_abs)

                gl_list = frappe.db.get_list("GL Entry", {"voucher_no": sales_invoice.name})
                if len(gl_list) > 0:
                    gl = frappe.db.get_value('GL Entry', gl_list[0].get('name'),
                                             ['creation', 'modified', 'modified_by', 'owner', 'posting_date'])

                sql_1 = """INSERT INTO `tabGL Entry` (name, creation, modified, modified_by, owner, posting_date, account, party_type, party,
                 cost_center, against_voucher_type, against_voucher, debit, credit, account_currency, debit_in_account_currency, credit_in_account_currency,
                  against, voucher_type, voucher_no, remarks, is_opening, is_advance, fiscal_year, company, is_cancelled, docstatus, to_rename) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', 
                  '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')""".format(frappe.generate_hash(txt="", length=10), gl[0], gl[1],
                                                                                                        gl[2], gl[3],
                                                                                                        gl[4],
                                                                                                        'Debtors - BBB',
                                                                                                        "Customer",
                                                                                                        sales_invoice.customer,
                                                                                                        sales_invoice.cost_center,
                                                                                                        "Sales Invoice",
                                                                                                        sales_invoice.name,
                                                                                                        change_amount_abs,
                                                                                                        0.0, "BDT",
                                                                                                        change_amount_abs,
                                                                                                        0.0,
                                                                                                        sales_invoice.account_for_change_amount,
                                                                                                        "Sales Invoice",
                                                                                                        sales_invoice.name,
                                                                                                        "No Remarks",
                                                                                                        "No", "No",
                                                                                                        year,
                                                                                                        sales_invoice.company,
                                                                                                        0, 1, 1)

                sql_2 = """INSERT INTO `tabGL Entry` (name, creation, modified, modified_by, owner, posting_date, account, party_type, party,
                 cost_center, against_voucher_type, against_voucher, debit, credit, account_currency, debit_in_account_currency, credit_in_account_currency,
                  against, voucher_type, voucher_no, remarks, is_opening, is_advance, fiscal_year, company, is_cancelled, docstatus, to_rename) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', 
                  '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')""".format(frappe.generate_hash(txt="", length=10), gl[0], gl[1],
                                                                                                        gl[2], gl[3],
                                                                                                        gl[4],
                                                                                                        sales_invoice.account_for_change_amount,
                                                                                                        None,
                                                                                                        None,
                                                                                                        sales_invoice.cost_center,
                                                                                                        "Sales Invoice",
                                                                                                        sales_invoice.name,
                                                                                                        0.0,
                                                                                                        change_amount_abs,
                                                                                                        "BDT",
                                                                                                        0.0,
                                                                                                        change_amount_abs,
                                                                                                        sales_invoice.customer,
                                                                                                        "Sales Invoice",
                                                                                                        sales_invoice.name,
                                                                                                        "No Remarks",
                                                                                                        "No", "No",
                                                                                                        year,
                                                                                                        sales_invoice.company,
                                                                                                        0, 1, 1)



                if sales_invoice.is_return == 1:
                    frappe.db.sql(sql_1)
                    frappe.db.sql(sql_2)
                    frappe.db.set_value('Sales Invoice', sales_invoice.name, 'outstanding_amount', 0)
                    frappe.db.set_value('Sales Invoice', sales_invoice.name, 'change_amount', change_amount_abs)
                    frappe.db.set_value('Sales Invoice', sales_invoice.name, 'base_change_amount', change_amount_abs)
                    frappe.db.set_value('Sales Invoice', sales_invoice.name, 'status', 'Return')
                    frappe.db.commit()
                    # print("s 1", sales_invoice.name)
                # else:
                    # frappe.db.set_value('Sales Invoice', sales_invoice.name, 'status', 'Paid')
                # frappe.db.commit()
                #     print("s 2", sales_invoice.name)
            # else:
            #     frappe.db.set_value('Sales Invoice', sales_invoice.name, 'outstanding_amount', 0)
            #     if sales_invoice.is_return == 1:
            #         frappe.db.set_value('Sales Invoice', sales_invoice.name, 'status', 'Return')
            #     else:
            #         frappe.db.set_value('Sales Invoice', sales_invoice.name, 'status', 'Paid')
            #     frappe.db.commit()
            #     print(sales_invoice.name)

        # elif sales_invoice.rounded_total < 0 and sales_invoice.paid_amount > sales_invoice.rounded_total:
        #     if sales_invoice.outstanding_amount < 0 and sales_invoice.is_return == 1:
        #         frappe.db.set_value('Sales Invoice', sales_invoice.name, 'outstanding_amount', 0)
        #         frappe.db.commit()
        #         print(sales_invoice.name)


from erpnext.accounts.report.accounts_receivable.accounts_receivable import ReceivablePayableReport


def get_accounts_receivable_invoices():
    # args = {
    #     "party_type": "Customer",
    #     "naming_by": ["Selling Settings", "cust_master_name"],
    # }
    # filters = {'company': 'BD Budget Beauty', 'report_date': '2023-04-05', 'ageing_based_on': 'Due Date', 'range1': 30,
    #  'range2': 60, 'range3': 90, 'range4': 120}
    # return ReceivablePayableReport(filters).run(args)

    sales_invoices = frappe.db.get_list('Sales Invoice', {'docstatus': 1, 'outstanding_amount': ["!=", 0]}, 'name')
    return sales_invoices


@frappe.whitelist()
def update_customers_dob():
    customer_list = frappe.db.get_list('Customer', ['name', 'birth_day', 'birth_month', 'birth_year', 'dob'])
    for customer in customer_list[0:1000]:
        if not customer.get('dob'):
            birth_year = 1997 if customer.get('birth_year') == 0 else customer.get('birth_year')
            birth_month = 4 if customer.get('birth_month') == 0 else customer.get('birth_month')
            birth_day = 13 if customer.get('birth_day') == 0 else customer.get('birth_day')
            birthday_str = str(birth_year) + '-' + str(birth_month) + '-' + str(birth_day)
            date_format = getdate(birthday_str)
            frappe.db.set_value('Customer', customer.get('name'), 'dob', date_format)


def update_woocommerce_stock(doc, method):
    from woocommerce import API
    woocommerce_settings = frappe.get_doc("Woocommerce Settings")
    if doc.voucher_type != 'Woocommerce Order' and woocommerce_settings.disabled == 0:
        bin = frappe.db.get_value("Bin", {'item_code': doc.item_code, 'warehouse': doc.warehouse}, 'actual_qty', as_dict=1)

        if woocommerce_settings.warehouse == doc.warehouse and bin:
            pre_qty = bin.get('actual_qty')
            incoming_value = doc.actual_qty
            woocommerce_id = frappe.db.get_value('Item', doc.item_code, 'woocommerce_id')

            if woocommerce_id and bin:
                wcapi = API(
                    url=woocommerce_settings.woocommerce_server_url,
                    consumer_key=woocommerce_settings.api_consumer_key,
                    consumer_secret=woocommerce_settings.api_consumer_secret,
                    wp_api=True,
                    version="wc/v3",
                    query_string_auth=True,
                )
                data = {
                    "stock_quantity": flt(pre_qty) + flt(incoming_value) if incoming_value else flt(doc.qty_after_transaction),
                    "manage_stock": True
                }
                url = "products/" + str(woocommerce_id)
                wcapi.put(url, data).json()
        
    
    