import frappe


def before_submit(doc, method):
    num = doc.grand_total
    if num is not None:

        float_number = float(num)
        int_number = int(float_number)
        divisible_number = (int_number // 5) * 5
        adjustment = float_number - divisible_number
        print(type(doc.rounded_total), " ",doc.rounded_total, " ",type(divisible_number), " ",divisible_number)
        print(float(doc.rounded_total) == float(divisible_number), " == ", float(doc.rounded_total) == float(divisible_number + 5))
        if float(doc.rounded_total) == float(divisible_number) or float(doc.rounded_total) == float(divisible_number + 5):
            pass
        elif adjustment < 2.50:
            doc.rounded_total = divisible_number
            doc.rounded_adjustment = -(adjustment) if adjustment != 0.0 else adjustment
            doc.save()
        elif adjustment > 2.49:
            doc.rounded_total = divisible_number + 5
            doc.rounded_adjustment = rounding_total - float_number
            doc.save()
