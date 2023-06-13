import json

import frappe
from frappe.utils import getdate
from frappe.model.mapper import map_child_doc, map_doc
from frappe import _
from frappe.core.page.background_jobs.background_jobs import get_info
from frappe.utils.background_jobs import enqueue
from frappe.utils.scheduler import is_scheduler_inactive

from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry


class CustomPOSClosingEntry(POSClosingEntry):
    def __init__(self, *args, **kwargs):
        super(CustomPOSClosingEntry, self).__init__(*args, **kwargs)
        
    def on_submit(self):
        consolidate_pos_invoices(closing_entry=self)

    def on_cancel(self):
        unconsolidate_pos_invoices(closing_entry=self)
        

def consolidate_pos_invoices(pos_invoices=None, closing_entry=None):
    pos_invoices = pos_invoices or (
        closing_entry and closing_entry.get("pos_transactions"))
    if not pos_invoices:
        frappe.throw(_("There must be at lest one invoice"),
                title=_("Invoice not found"))

    if len(pos_invoices) >= 10 and closing_entry:
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
            closing_entry.db_set("error_message", error_message)
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
    enqueued_jobs = [d.get("job_name") for d in get_info()]
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
            now=frappe.conf.developer_mode or frappe.flags.in_test
            
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
            sales_invoice = process_merging_into_sales_invoice(pos_invoice)
            update_pos_invoices(pos_invoice, sales_invoice, credit_note)
    if returns:
        for pos_invoice in returns:
            credit_note = process_merging_into_credit_note(pos_invoice)
            update_pos_invoices(pos_invoice, sales_invoice, credit_note)


def cancel_sales_invoices(pos_invoices):
    pos_invoice_docs = [
        frappe.get_doc("POS Invoice", d.pos_invoice) for d in pos_invoices
    ]
    for pos_invoice in pos_invoice_docs:
        sales_invoice_name = pos_invoice.consolidated_invoice
        update_pos_invoices(pos_invoice)
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


def merge_pos_invoice_into(invoice, doc):
    items, payments, taxes = [], [], []
    loyalty_amount_sum, loyalty_points_sum = 0, 0
    invoice_name = None
    naming_series = None
    posting_date = None
    loyalty_amount_sum, loyalty_points_sum, idx = 0, 0, 1
    invoice_name = "SINV-" + doc.name
    naming_series = "SINV-" + doc.naming_series
    posting_date = getdate(doc.posting_date)

    map_doc(doc, invoice, table_map={"doctype": invoice.doctype})

    if doc.redeem_loyalty_points:
        invoice.loyalty_redemption_account = doc.loyalty_redemption_account
        invoice.loyalty_redemption_cost_center = doc.loyalty_redemption_cost_center
        loyalty_points_sum += doc.loyalty_points
        loyalty_amount_sum += doc.loyalty_amount

    for item in doc.get("items"):
        si_item = map_child_doc(
            item, invoice, {"doctype": "Sales Invoice Item"})
        items.append(si_item)

    for tax in doc.get("taxes"):
        si_taxes = map_child_doc(
            tax, invoice, {"doctype": "Sales Taxes and Charges"})
        taxes.append(si_taxes)

    for payment in doc.get("payments"):
        payments.append(payment)

    if loyalty_points_sum:
        invoice.redeem_loyalty_points = 1
        invoice.loyalty_points = loyalty_points_sum
        invoice.loyalty_amount = loyalty_amount_sum

    # rabiul_new
    invoice.set("items", items)
    invoice.set("payments", payments)
    invoice.set("taxes", taxes)
    invoice.set("rounding_adjustment", doc.rounding_adjustment)
    invoice.set("base_rounding_adjustment", doc.base_rounding_adjustment)
    invoice.set("rounded_total", doc.rounded_total)
    invoice.set("base_rounded_total", doc.base_rounded_total)
    invoice.set("naming_series", naming_series)
    invoice.set("name", invoice_name)
    invoice.set("posting_date", posting_date)
    invoice.set("change_amount", doc.change_amount)
    invoice.set("base_change_amount", doc.base_change_amount)
    invoice.set("additional_discount_percentage",
                doc.additional_discount_percentage)
    invoice.set("discount_amount", doc.discount_amount)
    invoice.set("taxes_and_charges", doc.taxes_and_charges)
    invoice.set("ignore_pricing_rule", doc.ignore_pricing_rule)

    invoice.customer = doc.customer

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
    print("SI Name", si_name)
    si = frappe.get_doc("Sales Invoice", si_name)
    print("SI", si)
    si.flags.ignore_validate = True
    si.cancel()
