import frappe
from frappe.utils import flt, get_datetime
from erpnext.accounts.general_ledger import make_gl_entries


def validate(doc, method):
    total_closing_amount = 0
    rounded_total = 0
    link_invoices = doc.pos_transactions
    for link_invoice in link_invoices:
        pos_rounded_total = frappe.db.get_value(
            'POS Invoice', link_invoice.pos_invoice, 'rounded_total')
        rounded_total += pos_rounded_total

    doc.rounded_total = rounded_total

    payment_reconciliation = doc.payment_reconciliation
    for payment in payment_reconciliation:
        one_thousand_taka_note = payment.one_thousand_taka_note if payment.one_thousand_taka_note else 0
        five_hundred_taka_note = payment.five_hundred_taka_note if payment.five_hundred_taka_note else 0
        two_hundred_taka_note = payment.two_hundred_taka_note if payment.two_hundred_taka_note else 0
        one_hundred_taka_note = payment.one_hundred_taka_note if payment.one_hundred_taka_note else 0
        fifty_taka_note = payment.fifty_taka_note if payment.fifty_taka_note else 0
        twenty_taka_note = payment.twenty_taka_note if payment.twenty_taka_note else 0
        ten_taka_note = payment.ten_taka_note if payment.ten_taka_note else 0
        five_taka_note = payment.five_taka_note if payment.five_taka_note else 0
        five_taka_coin = payment.five_taka_coin if payment.five_taka_coin else 0
        two_taka_note = payment.two_taka_note if payment.two_taka_note else 0
        two_taka_coin = payment.two_taka_coin if payment.two_taka_coin else 0
        one_taka_note = payment.one_taka_note if payment.one_taka_note else 0
        one_taka_coin = payment.one_taka_coin if payment.one_taka_coin else 0

        total_amount = (
            1000 * one_thousand_taka_note + 500 * five_hundred_taka_note + 200 * two_hundred_taka_note +
            100 * one_hundred_taka_note + 50 * fifty_taka_note + 20 * twenty_taka_note + 10 * ten_taka_note +
            5 * five_taka_note + 5 * five_taka_coin + 2 * two_taka_note + 2 * two_taka_coin + one_taka_note + one_taka_coin)
        payment_types = str(payment.mode_of_payment).split(' ')
        if "Cash" in payment_types:
            payment.closing_amount = total_amount

        payment.total_amount = total_amount
        payment.withdrawal_amount = total_amount - payment.opening_amount

        if int(payment.expected_amount) > 0 and (int(payment.closing_amount) == int(payment.expected_amount)):
            payment.closing_status = 'Matched'
        elif int(payment.closing_amount) != int(payment.expected_amount):
            payment.closing_status = 'Mismatched'
        else:
            payment.closing_status = ''

        total_closing_amount += payment.closing_amount

    if int(total_closing_amount) != int(doc.rounded_total):
        frappe.msgprint('Closing Amount And Rounded Total Not Matched',
                        indicator="red", title="Warning")
    elif int(total_closing_amount) == int(doc.rounded_total):
        frappe.msgprint(
            'Closing Amount And Rounded Total Matched', indicator="green")


@frappe.whitelist()
def get_pos_invoices(start, end, pos_profile, user):
    data = frappe.db.sql(
        """
	select
		name, timestamp(posting_date, posting_time) as "timestamp"
	from
		`tabPOS Invoice`
	where
		owner = %s and docstatus = 1 and pos_profile = %s and ifnull(consolidated_invoice,'') = '' order by timestamp asc
	""",
        (user, pos_profile),
        as_dict=1,
    )

    data = list(
        filter(lambda d: get_datetime(start) <= get_datetime(
            d.timestamp) <= get_datetime(end), data)
    )
    # need to get taxes and payments so can't avoid get_doc
    data = [frappe.get_doc("POS Invoice", d.name).as_dict() for d in data]

    return data


@frappe.whitelist()
def get_advance_booking(start, end, pos_profile, user):
    data = frappe.db.sql(
        """
	select
		name, timestamp(posting_date, posting_time) as "timestamp"
	from
		`tabAdvance Booking`
	where
		owner = %s and docstatus = 1 and pos_profile = %s order by timestamp asc
	""",
        (user, pos_profile),
        as_dict=1,
    )
    data = list(
        filter(lambda d: get_datetime(start) <= get_datetime(
            d.timestamp) <= get_datetime(end), data)
    )
    # need to get taxes and payments so can't avoid get_doc
    data = [frappe.get_doc("Advance Booking", d.name).as_dict() for d in data]

    return data
