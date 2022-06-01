import frappe
import json
from frappe.utils import money_in_words


def after_insert(doc, method):
    num = doc.grand_total
    if num is not None:
        float_number = float(num)
        int_number = int(float_number)
        divisible_number = (int_number // 5) * 5
        adjustment = abs(float_number - divisible_number)
        # print(type(doc.rounded_total), " ",doc.rounded_total, " ",type(divisible_number), " ",divisible_number)
        # print(float(doc.rounded_total) == float(divisible_number), " == ", float(doc.rounded_total) == float(divisible_number + 5))
        payments = doc.payments
        paid_amount = 0
        for payment in payments:
            paid_amount += payment.amount

        if adjustment < 2.50:
            rounding_adjustment = -(adjustment) if adjustment != 0.0 else adjustment
            change_amount = (paid_amount - divisible_number) if (paid_amount - divisible_number) > 0 else 0
            outstanding_amount = (divisible_number - paid_amount) if (divisible_number - paid_amount) > 0 else 0

            in_words = money_in_words(divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("POS Invoice", doc.name, "grand_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "outstanding_amount", outstanding_amount)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)
            if outstanding_amount == 0:
                frappe.db.set_value("POS Invoice", doc.name, "status", "Paid")

        elif adjustment > 2.49:
            rounding_adjustment = (divisible_number + 5) - float_number
            change_amount = (paid_amount - (divisible_number + 5)) if (paid_amount - (divisible_number + 5)) > 0 else 0
            outstanding_amount = ((divisible_number + 5) - paid_amount) if ((divisible_number + 5) - paid_amount) > 0 else 0

            in_words = money_in_words(divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("POS Invoice", doc.name, "grand_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "outstanding_amount", outstanding_amount)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)
            if outstanding_amount == 0:
                frappe.db.set_value("POS Invoice", doc.name, "status", "Paid")


def before_submit(doc, method):
    num = doc.grand_total
    if num is not None:
        float_number = float(num)
        int_number = int(float_number)
        divisible_number = (int_number // 5) * 5
        adjustment = float_number - divisible_number
        # print(type(doc.rounded_total), " ",doc.rounded_total, " ",type(divisible_number), " ",divisible_number)
        # print(float(doc.rounded_total) == float(divisible_number), " == ", float(doc.rounded_total) == float(divisible_number + 5))
        payments = doc.payments
        paid_amount = 0
        for payment in payments:
            paid_amount += payment.amount

        if float(doc.rounded_total) == float(divisible_number) or float(doc.rounded_total) == float(
                divisible_number + 5):
            pass
        elif adjustment < 2.50:
            rounding_adjustment = -(adjustment) if adjustment != 0.0 else adjustment
            print("<2.50 ", rounding_adjustment)
            change_amount = (paid_amount - divisible_number) if (paid_amount - divisible_number) > 0 else 0
            outstanding_amount = (divisible_number - paid_amount) if (divisible_number - paid_amount) > 0 else 0
            in_words = money_in_words(divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("POS Invoice", doc.name, "grand_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "outstanding_amount", outstanding_amount)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)

        elif adjustment > 2.49:
            rounding_adjustment = divisible_number - float_number
            print(">2.49 ", rounding_adjustment)
            change_amount = (paid_amount - (divisible_number + 5)) if (paid_amount - (divisible_number + 5)) > 0 else 0
            outstanding_amount = (divisible_number - paid_amount) if (divisible_number - paid_amount) > 0 else 0
            in_words = money_in_words(divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "in_words", in_words)
            frappe.db.set_value("POS Invoice", doc.name, "grand_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", paid_amount)
            frappe.db.set_value("POS Invoice", doc.name, "change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "base_change_amount", change_amount)
            frappe.db.set_value("POS Invoice", doc.name, "outstanding_amount", outstanding_amount)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)


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

    if search_term and status:
        # invoices_by_customer = frappe.db.get_all(
        #     "POS Invoice",
        #     filters={"customer": ["like", "%{}%".format(search_term)], "status": status, 'owner': frappe.session.user},
        #     fields=fields, limit=limit
        # )
        invoices_by_name = frappe.db.get_all(
            "POS Invoice",
            filters={"name": ["like", "%{}%".format(search_term)], "status": status, 'owner': frappe.session.user},
            fields=fields, limit=limit
        )

        invoice_list = invoices_by_name
        # invoice_list = invoices_by_customer + invoices_by_name
    elif status:
        invoice_list = frappe.db.get_all("POS Invoice", filters={"status": status, 'owner': frappe.session.user}, fields=fields, limit=limit)

    return invoice_list
