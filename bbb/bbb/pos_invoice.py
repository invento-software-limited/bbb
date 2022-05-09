import frappe
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
            frappe.db.set_value("POS Invoice", doc.name, "rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "paid_amount", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "base_paid_amount", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "rounding_adjustment", rounding_adjustment)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounded_total", divisible_number + 5)
            frappe.db.set_value("POS Invoice", doc.name, "base_rounding_adjustment", rounding_adjustment)
