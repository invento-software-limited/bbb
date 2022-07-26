# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe import _, msgprint, throw
from frappe.utils import (
    add_days,
    add_months,
    cint,
    cstr,
    flt,
    formatdate,
    get_link_to_form,
    getdate,
    nowdate,
)

from erpnext.accounts.deferred_revenue import validate_service_stop_date
from erpnext.accounts.doctype.loyalty_program.loyalty_program import (
    get_loyalty_program_details_with_points,
    validate_loyalty_points,
)
from erpnext.stock.doctype.batch.batch import set_batch_nos

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

form_grid_templates = {
    "items": "templates/form_grid/item_grid.html"
}


class CustomSalesInvoice(SalesInvoice):
    def __init__(self, *args, **kwargs):
        super(CustomSalesInvoice, self).__init__(*args, **kwargs)
        self.status_updater = [{
            'source_dt': 'Sales Invoice Item',
            'target_field': 'billed_amt',
            'target_ref_field': 'amount',
            'target_dt': 'Sales Order Item',
            'join_field': 'so_detail',
            'target_parent_dt': 'Sales Order',
            'target_parent_field': 'per_billed',
            'source_field': 'amount',
            'percent_join_field': 'sales_order',
            'status_field': 'billing_status',
            'keyword': 'Billed',
            'overflow_type': 'billing'
        }]

    def verify_payment_amount_is_negative(self):
        pass
        # for entry in self.payments:
        #     if entry.amount > 0:
        #         frappe.throw(_("Row #{0} (Payment Table): Amount must be negative").format(entry.idx))

    def validate_pos(self):
        if self.is_return:
            invoice_total = self.rounded_total or self.grand_total
            # if flt(self.paid_amount) + flt(self.write_off_amount) - flt(invoice_total) > 1.0 / (
            #         10.0 ** (self.precision("grand_total") + 1.0)
            # ):
            #     frappe.throw(_("Paid amount + Write Off Amount can not be greater than Grand Total"))

    def validate_qty(self):
        """Validates qty at row level"""
        self.item_allowance = {}
        self.global_qty_allowance = None
        self.global_amount_allowance = None

        for args in self.status_updater:
            if "target_ref_field" not in args:
                # if target_ref_field is not specified, the programmer does not want to validate qty / amount
                continue

            # get unique transactions to update
            for d in self.get_all_children():
                if hasattr(d, 'qty') and d.qty < 0 and not self.get('is_return'):
                    frappe.throw(_("For an item {0}, quantity must be positive number").format(d.item_code))
                # munim fine
                # if hasattr(d, 'qty') and d.qty > 0 and self.get('is_return'):
                # 	frappe.throw(_("For an item {0}, quantity must be negative number").format(d.item_code))

                if d.doctype == args['source_dt'] and d.get(args["join_field"]):
                    args['name'] = d.get(args['join_field'])

                    # get all qty where qty > target_field
                    item = frappe.db.sql("""select item_code, `{target_ref_field}`,
                        `{target_field}`, parenttype, parent from `tab{target_dt}`
                        where `{target_ref_field}` < `{target_field}`
                        and name=%s and docstatus=1""".format(**args),
                                         args['name'], as_dict=1)
                    if item:
                        item = item[0]
                        item['idx'] = d.idx
                        item['target_ref_field'] = args['target_ref_field'].replace('_', ' ')

                        # if not item[args['target_ref_field']]:
                        # 	msgprint(_("Note: System will not check over-delivery and over-booking for Item {0} as quantity or amount is 0").format(item.item_code))
                        if args.get('no_allowance'):
                            item['reduce_by'] = item[args['target_field']] - item[args['target_ref_field']]
                            if item['reduce_by'] > .01:
                                self.limits_crossed_error(args, item, "qty")

                        elif item[args['target_ref_field']]:
                            self.check_overflow_with_allowance(item, args)
