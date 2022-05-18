import frappe
import json
from frappe.utils import money_in_words


def after_insert(doc, method):
    num = doc.grand_total
    if num is not None:
        float_number = float(num)
        int_number = int(float_number)
        divisible_number = (int_number // 5) * 5
        adjustment = float_number - divisible_number
        # print(type(doc.rounded_total), " ",doc.rounded_total, " ",type(divisible_number), " ",divisible_number)
        # print(float(doc.rounded_total) == float(divisible_number), " == ", float(doc.rounded_total) == float(divisible_number + 5))
        if float(doc.rounded_total) == float(divisible_number) or float(doc.rounded_total) == float(
                divisible_number + 5):
            pass
        elif adjustment < 2.50:
            rounding_adjustment = -(adjustment) if adjustment != 0.0 else adjustment
            in_words = money_in_words(divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("POS Invoice", doc.name, "grand_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)

        elif adjustment > 2.49:
            rounding_adjustment = divisible_number - float_number
            in_words = money_in_words(divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("POS Invoice", doc.name, "grand_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)


def before_submit(doc, method):
    num = doc.grand_total
    if num is not None:
        float_number = float(num)
        int_number = int(float_number)
        divisible_number = (int_number // 5) * 5
        adjustment = float_number - divisible_number
        # print(type(doc.rounded_total), " ",doc.rounded_total, " ",type(divisible_number), " ",divisible_number)
        # print(float(doc.rounded_total) == float(divisible_number), " == ", float(doc.rounded_total) == float(divisible_number + 5))
        if float(doc.rounded_total) == float(divisible_number) or float(doc.rounded_total) == float(
                divisible_number + 5):
            pass
        elif adjustment < 2.50:
            rounding_adjustment = -(adjustment) if adjustment != 0.0 else adjustment
            in_words = money_in_words(divisible_number)
            frappe.db.set_value("Sales Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("Sales Invoice", doc.name, "rounded_total", divisible_number)
            frappe.db.set_value("Sales Invoice", doc.name, "paid_amount", divisible_number)
            frappe.db.set_value("Sales Invoice", doc.name, "base_paid_amount", divisible_number)
            frappe.db.set_value("Sales Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("Sales Invoice", doc.name, "base_rounded_total", divisible_number)
            frappe.db.set_value("Sales Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)

        elif adjustment > 2.49:
            rounding_adjustment = divisible_number - float_number
            in_words = money_in_words(divisible_number + 5)
            frappe.db.set_value("Sales Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("Sales Invoice", doc.name, "rounded_total", divisible_number + 5)
            frappe.db.set_value("Sales Invoice", doc.name, "paid_amount", divisible_number + 5)
            frappe.db.set_value("Sales Invoice", doc.name, "base_paid_amount", divisible_number + 5)
            frappe.db.set_value("Sales Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("Sales Invoice", doc.name, "base_rounded_total", divisible_number + 5)
            frappe.db.set_value("Sales Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)


@frappe.whitelist()
def set_pos_cached_data(invoice_data=None):
    invoice_data = json.loads(invoice_data)
    key_list = ['pos_customer', 'pos_served_by', 'pos_ignore_pricing_rule']
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


@frappe.whitelist()
def get_pos_cached_data():
    # customer = frappe.cache().delete_value('pos_items')
    # customer = frappe.cache().delete_value('pos_customer')
    # customer = frappe.cache().delete_value('pos_ignore_pricing_rule')
    # customer = frappe.cache().delete_value('pos_items')
    customer = frappe.cache().get_value('pos_customer')
    if customer:
        data = {}
        data['pos_customer'] = customer
        data['pos_served_by'] = frappe.cache().get_value('pos_served_by')
        data['pos_ignore_pricing_rule'] = frappe.cache().get_value('pos_ignore_pricing_rule')
        data['pos_items'] = frappe.cache().get_value('pos_items')
        return data
    else:
        return {}
