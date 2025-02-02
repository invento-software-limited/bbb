import json

import frappe
from frappe.utils import getdate
from frappe.model.mapper import map_child_doc, map_doc
from frappe import _
from frappe.utils.background_jobs import enqueue, get_jobs
from frappe.utils.scheduler import is_scheduler_inactive
from frappe.utils import (
    flt,
    formatdate,
    getdate,
    now,
)
import json

from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry
from erpnext.accounts.general_ledger import make_gl_entries, process_gl_map
from erpnext.accounts.utils import get_account_currency, get_fiscal_years, validate_fiscal_year
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)

from bbb.bbb.pos_closing_entry import get_pos_invoices

class CustomPOSClosingEntry(POSClosingEntry):
    def __init__(self, *args, **kwargs):
        super(CustomPOSClosingEntry, self).__init__(*args, **kwargs)

    def on_submit(self):
        start = frappe.utils.get_datetime_str(self.period_start_date)
        end = frappe.utils.get_datetime_str(frappe.utils.now())
        pos_profile = self.pos_profile
        user = self.user

        pos_invoices = get_pos_invoices(start, end, pos_profile, user)
        if len(pos_invoices) != len(self.pos_transactions):
            frappe.throw(_("Some invoices are missing or not loaded successfully. You must save the document again"))

        # CREATE INDEX idx_sales_invoice_pos ON `tabSales Invoice` (`pos_profile`, `posting_date`);
        # CREATE INDEX idx_pos_closing_entry_docstatus ON `tabPOS Closing Entry` (`docstatus`);


        # self.create_gl_entries()
        consolidate_pos_invoices(closing_entry=self)

    def on_cancel(self):
        unconsolidate_pos_invoices(closing_entry=self)
        # self.cancel_gl_entry()

    def validate(self):
        super(CustomPOSClosingEntry, self).validate()
        fiscal_years = get_fiscal_years(
            self.posting_date, company=self.company)
        if len(fiscal_years) > 1:
            frappe.throw(
                _("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
                    formatdate(self.posting_date)
                )
            )
        else:
            fiscal_year = fiscal_years[0][0]

    def create_gl_entries(self, cancel=False):
        # dict_1 = frappe._dict({'company': 'Orkas Glam Bar And Revive Spa', 'posting_date': '2023-06-21', 'fiscal_year': '2023', 'voucher_type': 'Payment Entry', 'voucher_no': 'ACC-PAY-2023-00003', 'remarks': 'Amount BDT 1000 received from tamanna - 250\nTransaction reference no 132666 dated 2023-06-21', 'debit': 1000.0,
        #                       'credit': 0, 'debit_in_account_currency': 1000, 'credit_in_account_currency': 0, 'is_opening': 'No', 'party_type': None, 'party': None, 'project': None, 'post_net_value': None, 'account': 'City Bank Ltd - SPA', 'account_currency': 'BDT', 'against': 'tamanna - 250', 'cost_center': 'Mirpur Parlour - SPA'})
        # dict_2 = frappe._dict({'company': 'Orkas Glam Bar And Revive Spa', 'posting_date': '2023-06-21', 'fiscal_year': '2023', 'voucher_type': 'Payment Entry', 'voucher_no': 'ACC-PAY-2023-00003', 'remarks': 'Amount BDT 1000 received from tamanna - 250\nTransaction reference no 132666 dated 2023-06-21', 'debit': 0, 'credit': 1000.0,
        #                       'debit_in_account_currency': 0, 'credit_in_account_currency': 1000.0, 'is_opening': 'No', 'party_type': 'Customer', 'party': 'tamanna - 250', 'project': None, 'post_net_value': None, 'account': 'Debtors - SPA', 'against': 'City Bank Ltd - SPA', 'account_currency': 'BDT', 'cost_center': 'Mirpur Parlour - SPA'})
        # data = [dict_2, dict_1]

        advance_booking_reference = self.advance_booking_reference
        for advance_booking in advance_booking_reference:
            advance_booking_doc = frappe.get_doc(
                'Advance Booking', advance_booking.advance_booking)
            payments = advance_booking_doc.payments
            for payment in payments:
                gl_entries = []
                if payment.amount > 0:
                    self.add_party_gl_entries(
                        gl_entries, advance_booking_doc, payment)
                    gl_entries = process_gl_map(gl_entries)
                    make_gl_entries(gl_entries)

    def cancel_gl_entry(self):
        advance_booking_reference = self.advance_booking_reference
        for advance_booking in advance_booking_reference:
            advance_booking_doc = frappe.get_doc(
                'Advance Booking', advance_booking.advance_booking)
            gl_entry_doc = frappe.get_list(
                'GL Entry', {'voucher_no': advance_booking_doc.name})
            for gle in gl_entry_doc:
                frappe.db.set_value('GL Entry', gle.name, 'is_cancelled', 1)
            payments = advance_booking_doc.payments
            for payment in payments:
                gl_entries = []
                if payment.amount > 0:
                    self.add_party_gl_entries(
                        gl_entries, advance_booking_doc, payment)
                    gl_entries = process_gl_map(gl_entries)
                    make_gl_entries(gl_entries, True)

    def add_party_gl_entries(self, gl_entries, advance_booking_doc, payment):
        fiscal_years = get_fiscal_years(
            advance_booking_doc.posting_date, company=self.company)
        if len(fiscal_years) > 1:
            frappe.throw(
                _("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
                    formatdate(advance_booking_doc.posting_date)
                )
            )
        else:
            fiscal_year = fiscal_years[0][0]
        dict_1 = frappe._dict(
            {
                'company': self.company,
                'posting_date': advance_booking_doc.posting_date,
                'fiscal_year': fiscal_year,
                'voucher_type': 'Advance Booking',
                'voucher_no': advance_booking_doc.name,
                'remarks': 'Amount BDT {} received from {}'.format(payment.amount, advance_booking_doc.customer),
                'debit': 0,
                'credit': payment.amount,
                'debit_in_account_currency': 0,
                'credit_in_account_currency': payment.amount,
                'is_opening': 'No',
                'party_type': 'Customer',
                'party': advance_booking_doc.customer,
                'project': None,
                'post_net_value': None,
                'account': 'Debtors - SPA',
                'against': payment.account,
                'account_currency': 'BDT',
                'is_advance': 'No',
                'cost_center': advance_booking_doc.cost_center
            }
        )
        gl_entries.append(dict_1)

        dict_2 = frappe._dict(
            {
                'company': self.company,
                'posting_date': advance_booking_doc.posting_date,
                'fiscal_year': fiscal_year,
                'voucher_type': 'Advance Booking',
                'voucher_no': advance_booking_doc.name,
                'remarks': 'Amount BDT {} received from {}'.format(payment.amount, advance_booking_doc.customer),
                'debit': payment.amount,
                'credit': 0,
                'debit_in_account_currency': payment.amount,
                'credit_in_account_currency': 0,
                'is_opening': 'No',
                'party_type': None,
                'party': None,
                'project': None,
                'post_net_value': None,
                'account': payment.account,
                'account_currency': 'BDT',
                'against': advance_booking_doc.customer,
                'is_advance': 'No',
                'cost_center': advance_booking_doc.cost_center
            })

        gl_entries.append(dict_2)


def consolidate_pos_invoices(pos_invoices=None, closing_entry=None):
    pos_invoices = pos_invoices or (
        closing_entry and closing_entry.get("pos_transactions"))
    advance_booking_reference = closing_entry.get("advance_booking_reference")
    if not pos_invoices and not advance_booking_reference:
        frappe.throw(_("There must be at lest one invoice"),
                     title=_("Invoice not found"))

    if len(pos_invoices) >= 1 and closing_entry:
        closing_entry.set_status(update=True, status="Queued")
        enqueue_job(
            create_merge_logs, pos_invoices=pos_invoices, closing_entry=closing_entry
        )
    else:
        create_merge_logs(pos_invoices, closing_entry)


def unconsolidate_pos_invoices(pos_invoices=None, closing_entry=None):
    pos_invoices = pos_invoices or (
        closing_entry and closing_entry.get("pos_transactions"))

    if len(pos_invoices) >= 10:
        closing_entry.set_status(update=True, status="Queued")
        enqueue_job(cancel_merge_logs, pos_invoices=pos_invoices,
                    closing_entry=closing_entry)
    else:
        cancel_merge_logs(pos_invoices, closing_entry)


def get_all_unconsolidated_invoices():
    filters = {
        "consolidated_invoice": ["in", ["", None]],
        "status": ["not in", ["Consolidated"]],
        "docstatus": 1,
    }
    pos_invoices = frappe.db.get_all(
        "POS Invoice",
        filters=filters,
        fields=[
            "name as pos_invoice",
            "posting_date",
            "grand_total",
            "customer",
            "is_return",
            "return_against",
        ],
    )

    return pos_invoices


def create_merge_logs(pos_invoices, closing_entry=None):
    try:
        create_sales_invoices(pos_invoices=pos_invoices)
        if closing_entry:
            closing_entry.set_status(update=True, status="Submitted")
            closing_entry.db_set("error_message", "")
            closing_entry.update_opening_entry()

    except Exception as e:
        frappe.db.rollback()
        message_log = frappe.message_log.pop() if frappe.message_log else str(e)
        error_message = safe_load_json(message_log)

        if closing_entry:
            closing_entry.set_status(update=True, status="Failed")
            closing_entry.db_set("error_message", json.dumps(error_message))
        raise

    finally:
        frappe.db.commit()
        frappe.publish_realtime("closing_process_complete", {
                                "user": frappe.session.user})


def cancel_merge_logs(pos_invoices, closing_entry=None):
    try:

        cancel_sales_invoices(pos_invoices=pos_invoices)
        if closing_entry:
            closing_entry.set_status(update=True, status="Cancelled")
            closing_entry.db_set("error_message", "")
            closing_entry.update_opening_entry(for_cancel=True)

    except Exception as e:
        frappe.db.rollback()
        message_log = frappe.message_log.pop() if frappe.message_log else str(e)
        error_message = safe_load_json(message_log)

        if closing_entry:
            closing_entry.set_status(update=True, status="Submitted")
            closing_entry.db_set("error_message", error_message)
        raise

    finally:
        frappe.db.commit()
        frappe.publish_realtime("closing_process_complete", {
                                "user": frappe.session.user})


def check_scheduler_status():
    if is_scheduler_inactive() and not frappe.flags.in_test:
        frappe.throw(_("Scheduler is inactive. Cannot enqueue job."),
                     title=_("Scheduler Inactive"))


def job_already_enqueued(job_name):
    # Check for enqueued jobs in the BackgroundJob doctype
    enqueued_jobs = frappe.get_all('BackgroundJob', filters={'status': 'Queued'}, fields=['job_name'])
    enqueued_jobs = [job['job_name'] for job in enqueued_jobs]
    
    # enqueued_jobs = [d.get("job_name") for d in get_jobs()]
    if job_name in enqueued_jobs:
        return True


def safe_load_json(message):
    try:
        json_message = json.loads(message).get("message")
    except Exception:
        json_message = message

    return json_message


def enqueue_job(job, **kwargs):
    check_scheduler_status()

    closing_entry = kwargs.get("closing_entry") or {}

    job_name = closing_entry.get("name")
    if not job_already_enqueued(job_name):
        enqueue(
            job,
            **kwargs,
            queue="long",
            timeout=50000,
            event="processing_merge_logs",
            job_name=job_name,
            # now=frappe.conf.developer_mode or frappe.flags.in_test
            now=False

        )

        if job == create_merge_logs:
            msg = _("POS Invoices will be consolidated in a background process")
        else:
            msg = _("POS Invoices will be unconsolidated in a background process")

        frappe.msgprint(msg, alert=1)


def create_sales_invoices(pos_invoices):
    pos_invoice_docs = [
        frappe.get_doc("POS Invoice", d.pos_invoice) for d in pos_invoices
    ]

    sales = [d for d in pos_invoice_docs if d.is_return == 0]
    returns = [d for d in pos_invoice_docs if d.is_return == 1]

    sales_invoice, credit_note = "", ""

    if sales:
        for pos_invoice in sales:
            if pos_invoice.status == "consolidated":
                continue
            sales_invoice = process_merging_into_sales_invoice(pos_invoice)
            update_pos_invoices(pos_invoice, sales_invoice, credit_note)
            update_advance_booking(doc=pos_invoice, sales_invoice=sales_invoice, cancel=False)
    if returns:
        for pos_invoice in returns:
            if pos_invoice.status == "consolidated":
                continue
            credit_note = process_merging_into_credit_note(pos_invoice)
            update_pos_invoices(pos_invoice, sales_invoice, credit_note)
            update_advance_booking(doc=pos_invoice, credit_note=credit_note, cancel=False)


def cancel_sales_invoices(pos_invoices):
    pos_invoice_docs = [
        frappe.get_doc("POS Invoice", d.pos_invoice) for d in pos_invoices
    ]
    for pos_invoice in pos_invoice_docs:
        sales_invoice_name = pos_invoice.consolidated_invoice
        update_pos_invoices(pos_invoice)
        update_advance_booking(doc=pos_invoice)
        cancel_linked_invoices(sales_invoice_name)


def process_merging_into_sales_invoice(doc):
    sales_invoice = get_new_sales_invoice(doc)
    sales_invoice = merge_pos_invoice_into(sales_invoice, doc)
    sales_invoice.is_consolidated = 1
    sales_invoice.set_posting_time = 1
    sales_invoice.save()
    sales_invoice.submit()
    
    return sales_invoice.name


def process_merging_into_credit_note(doc):
    credit_note = get_new_sales_invoice(doc)
    credit_note.is_return = 1
    credit_note = merge_pos_invoice_into(credit_note, doc)
    credit_note.is_consolidated = 1
    credit_note.set_posting_time = 1
    # TODO: return could be against multiple sales invoice which could also have been consolidated?
    # credit_note.return_against = self.consolidated_invoice
    credit_note.save()
    credit_note.submit()

    return credit_note.name


# def merge_pos_invoice_into(invoice, doc):
#     items, payments, taxes, advances = [], [], [], []
#     loyalty_amount_sum, loyalty_points_sum = 0, 0
#     loyalty_amount_sum, loyalty_points_sum, idx = 0, 0, 1
#     invoice_name = "SINV-" + doc.name
#     naming_series = "SINV-" + doc.naming_series
#     posting_date = getdate(doc.posting_date)

#     map_doc(doc, invoice, table_map={"doctype": invoice.doctype})

#     if doc.redeem_loyalty_points:
#         invoice.loyalty_redemption_account = doc.loyalty_redemption_account
#         invoice.loyalty_redemption_cost_center = doc.loyalty_redemption_cost_center
#         loyalty_points_sum += doc.loyalty_points
#         loyalty_amount_sum += doc.loyalty_amount

#     for item in doc.get("items"):
#         si_item = map_child_doc(
#             item, invoice, {"doctype": "Sales Invoice Item"})
#         items.append(si_item)
        
#     for adv in doc.get("advances"):
#         adv_detail = frappe._dict({
#             "parent": invoice.name,
# 			"parenttype": "Sales Invoice",
# 			"doctype": "Sales Invoice Advance",
# 			"reference_type": "Advance Booking",
# 			"reference_name": adv.reference_name,
# 			"remarks": adv.remarks,
# 			"advance_amount": flt(adv.advance_amount),
# 			"allocated_amount": flt(adv.allocated_amount),
# 			"ref_exchange_rate": 1
#         })
#         advances.append(adv_detail)

#     for tax in doc.get("taxes"):
#         si_taxes = map_child_doc(
#             tax, invoice, {"doctype": "Sales Taxes and Charges"})
#         taxes.append(si_taxes)

#     for payment in doc.get("payments"):
#         payments.append(payment)

#     if loyalty_points_sum:
#         invoice.redeem_loyalty_points = 1
#         invoice.loyalty_points = loyalty_points_sum
#         invoice.loyalty_amount = loyalty_amount_sum

#     # rabiul_new
#     invoice.set("items", items)
#     invoice.set("payments", payments)
#     invoice.set("taxes", taxes)
#     invoice.set("rounding_adjustment", doc.rounding_adjustment)
#     invoice.set("base_rounding_adjustment", doc.base_rounding_adjustment)
#     invoice.set("rounded_total", doc.rounded_total)
#     invoice.set("base_rounded_total", doc.base_rounded_total)
#     invoice.set("naming_series", naming_series)
#     invoice.set("name", invoice_name)
#     invoice.set("posting_date", posting_date)
#     invoice.set("additional_discount_percentage",
#                 doc.additional_discount_percentage)
#     invoice.set("discount_amount", doc.discount_amount)
#     invoice.set("taxes_and_charges", doc.taxes_and_charges)
#     invoice.set("ignore_pricing_rule", doc.ignore_pricing_rule)
#     invoice.set("allocate_advances_automatically", 1)
#     invoice.set("advance_booking_doc", doc.advance_booking_doc)
#     invoice.set("advances", advances)
#     invoice.set("total_advance", doc.total_advance)
#     invoice.set("outstanding_amount", 0)
#     invoice.customer = doc.customer
#     return invoice

def merge_pos_invoice_into(invoice, doc):
    items, payments, taxes, advances = [], [], [], []

    loyalty_amount_sum, loyalty_points_sum = 0, 0

    rounding_adjustment, base_rounding_adjustment = 0, 0
    rounded_total, base_rounded_total = 0, 0

    loyalty_amount_sum, loyalty_points_sum, idx = 0, 0, 1

    invoice_name = "SINV-" + doc.name
    naming_series = "SINV-" + doc.naming_series
    posting_date = getdate(doc.posting_date)

    map_doc(doc, invoice, table_map={ "doctype": invoice.doctype })

    if doc.redeem_loyalty_points:
        invoice.loyalty_redemption_account = doc.loyalty_redemption_account
        invoice.loyalty_redemption_cost_center = doc.loyalty_redemption_cost_center
        loyalty_points_sum += doc.loyalty_points
        loyalty_amount_sum += doc.loyalty_amount

    for item in doc.get('items'):

        item.rate = item.net_rate
        item.amount = item.net_amount
        item.base_amount = item.base_net_amount
        item.price_list_rate = 0
        si_item = map_child_doc(item, invoice, {"doctype": "Sales Invoice Item"})
        items.append(si_item)
            
    for adv in doc.get("advances"):
        adv_detail = frappe._dict({
            "parent": invoice.name,
            "parenttype": "Sales Invoice",
            "doctype": "Sales Invoice Advance",
            "reference_type": "Advance Booking",
            "reference_name": adv.reference_name,
            "remarks": adv.remarks,
            "advance_amount": flt(adv.advance_amount),
            "allocated_amount": flt(adv.allocated_amount),
            "ref_exchange_rate": 1
        })
        advances.append(adv_detail)

    for tax in doc.get('taxes'):
        tax.charge_type = 'Actual'
        tax.idx = idx
        idx += 1
        tax.included_in_print_rate = 0
        tax.tax_amount = tax.tax_amount_after_discount_amount
        tax.base_tax_amount = tax.base_tax_amount_after_discount_amount
        tax.item_wise_tax_detail = tax.item_wise_tax_detail
        taxes.append(tax)
    
    for payment in doc.get("payments"):
        payments.append(payment)

    rounding_adjustment += doc.rounding_adjustment
    rounded_total += doc.rounded_total
    base_rounding_adjustment += doc.base_rounding_adjustment
    base_rounded_total += doc.base_rounded_total


    if loyalty_points_sum:
        invoice.redeem_loyalty_points = 1
        invoice.loyalty_points = loyalty_points_sum
        invoice.loyalty_amount = loyalty_amount_sum

    invoice.set('items', items)
    invoice.set('payments', payments)
    invoice.set('taxes', taxes)
    invoice.set('rounding_adjustment',rounding_adjustment)
    invoice.set('base_rounding_adjustment',base_rounding_adjustment)
    invoice.set('rounded_total',rounded_total)
    invoice.set('base_rounded_total',base_rounded_total)
    invoice.set("allocate_advances_automatically", 1)
    invoice.set("advance_booking_doc", doc.advance_booking_doc)
    invoice.set("advances", advances)
    invoice.set("total_advance", doc.total_advance)
    invoice.set("outstanding_amount", 0)
    invoice.set("naming_series", naming_series)
    invoice.set("name", invoice_name)
    invoice.set("posting_date", posting_date)
    invoice.set("change_amount", doc.change_amount)
    invoice.set("base_change_amount", doc.base_change_amount)
    invoice.additional_discount_percentage = 0
    invoice.discount_amount = 0.0
    invoice.taxes_and_charges = None
    invoice.ignore_pricing_rule = 1
    invoice.customer = doc.customer

    # if self.merge_invoices_based_on == 'Customer Group':
    #     invoice.flags.ignore_pos_profile = True
    #     invoice.pos_profile = ''

    return invoice
  
def get_new_sales_invoice(doc):
    sales_invoice = frappe.new_doc("Sales Invoice")
    sales_invoice.customer = doc.customer
    sales_invoice.is_pos = 1

    return sales_invoice


def update_pos_invoices(doc, sales_invoice="", credit_note=""):
    doc.load_from_db()
    doc.update(
        {
            "consolidated_invoice": None
            if (sales_invoice == "" and credit_note == "")
            else (credit_note if doc.is_return else sales_invoice)
        }
    )
    doc.set_status(update=True)
    doc.save()


def cancel_linked_invoices(si_name):
    si = frappe.get_doc("Sales Invoice", si_name)
    si.flags.ignore_validate = True
    si.cancel()

def update_advance_booking(doc, sales_invoice="", credit_note="", cancel=True):
    adv_booking = frappe.db.get_value('POS Invoice', doc.name, ['advance_booking_doc'])
    if adv_booking:
        frappe.db.set_value("Advance Booking", adv_booking, 'status', 'To Deliver' if cancel else 'Completed')
        frappe.db.set_value("Advance Booking", adv_booking, 'consolidated_invoice', None if (sales_invoice == "" and credit_note == "") else (credit_note if doc.is_return else sales_invoice))
        frappe.db.set_value("Advance Booking", adv_booking, 'consolidated_pos_invoice', None if cancel == True else doc.name)

        if sales_invoice:
            frappe.db.sql(
                """UPDATE `tabGL Entry` SET is_cancelled = 1,
                modified=%s, modified_by=%s
                where voucher_type=%s and voucher_no=%s and is_cancelled = 0""",
                (now(), frappe.session.user, 'Advance Booking', adv_booking),
            )
        elif credit_note:
            frappe.db.sql(
                """UPDATE `tabGL Entry` SET is_cancelled = 0,
                modified=%s, modified_by=%s
                where voucher_type=%s and voucher_no=%s and is_cancelled = 0""",
                (now(), frappe.session.user, 'Advance Booking', adv_booking),
            )
            