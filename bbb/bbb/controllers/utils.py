import json

import frappe
import datetime
from frappe.permissions import get_doctypes_with_read
from frappe.utils import cint, cstr


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
        mrp_amount = float(item.qty) * float(item.price_list_rate)
        total_amount = float(item.qty) * float(item.rate)
        item_total_discount += (mrp_amount - total_amount)
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
