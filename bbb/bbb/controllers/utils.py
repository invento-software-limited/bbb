import frappe


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
