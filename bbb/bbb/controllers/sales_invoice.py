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

    def get_item_list(self):
        il = []
        for d in self.get("items"):
            if d.qty is None:
                frappe.throw(_("Row {0}: Qty is mandatory").format(d.idx))

            if self.has_product_bundle(d.item_code):
                for p in self.get("packed_items"):
                    if p.parent_detail_docname == d.name and p.parent_item == d.item_code:
                        # the packing details table's qty is already multiplied with parent's qty
                        il.append(
                            frappe._dict(
                                {
                                    "warehouse": p.warehouse or d.warehouse,
                                    "item_code": p.item_code,
                                    "qty": flt(p.qty),
                                    "uom": p.uom,
                                    "batch_no": cstr(p.batch_no).strip(),
                                    "serial_no": cstr(p.serial_no).strip(),
                                    "name": d.name,
                                    "target_warehouse": p.target_warehouse,
                                    "company": self.company,
                                    "voucher_type": self.doctype,
                                    "allow_zero_valuation": d.allow_zero_valuation_rate,
                                    "sales_invoice_item": d.get("sales_invoice_item"),
                                    "dn_detail": d.get("dn_detail"),
                                    "incoming_rate": p.get("incoming_rate"),
                                }
                            )
                        )

                        if self.sales_type == 'Distribution':
                            il.append(
                                frappe._dict(
                                    {
                                        "warehouse": 'Distribution - BBB',
                                        "item_code": p.item_code,
                                        "qty": flt(p.qty),
                                        "uom": p.uom,
                                        "batch_no": cstr(p.batch_no).strip(),
                                        "serial_no": cstr(p.serial_no).strip(),
                                        "name": d.name,
                                        "target_warehouse": '',
                                        "company": self.company,
                                        "voucher_type": self.doctype,
                                        "allow_zero_valuation": d.allow_zero_valuation_rate,
                                        "sales_invoice_item": d.get("sales_invoice_item"),
                                        "dn_detail": d.get("dn_detail"),
                                        "incoming_rate": p.get("incoming_rate"),
                                    }
                                )
                            )
            else:
                il.append(
                    frappe._dict(
                        {
                            "warehouse": d.warehouse,
                            "item_code": d.item_code,
                            "qty": d.stock_qty,
                            "uom": d.uom,
                            "stock_uom": d.stock_uom,
                            "conversion_factor": d.conversion_factor,
                            "batch_no": cstr(d.get("batch_no")).strip(),
                            "serial_no": cstr(d.get("serial_no")).strip(),
                            "name": d.name,
                            "target_warehouse": d.target_warehouse,
                            "company": self.company,
                            "voucher_type": self.doctype,
                            "allow_zero_valuation": d.allow_zero_valuation_rate,
                            "sales_invoice_item": d.get("sales_invoice_item"),
                            "dn_detail": d.get("dn_detail"),
                            "incoming_rate": d.get("incoming_rate"),
                        }
                    )
                )

                if self.sales_type == 'Distribution':
                    il.append(
                        frappe._dict(
                            {
                                "warehouse": 'Distribution - BBB',
                                "item_code": d.item_code,
                                "qty": d.stock_qty,
                                "uom": d.uom,
                                "stock_uom": d.stock_uom,
                                "conversion_factor": d.conversion_factor,
                                "batch_no": cstr(d.get("batch_no")).strip(),
                                "serial_no": cstr(d.get("serial_no")).strip(),
                                "name": d.name,
                                "target_warehouse": '',
                                "company": self.company,
                                "voucher_type": self.doctype,
                                "allow_zero_valuation": d.allow_zero_valuation_rate,
                                "sales_invoice_item": d.get("sales_invoice_item"),
                                "dn_detail": d.get("dn_detail"),
                                "incoming_rate": d.get("incoming_rate"),
                            }
                        )
                    )
        return il

    def update_stock_ledger(self):
        self.update_reserved_qty()

        sl_entries = []
        # Loop over items and packed items table
        for d in self.get_item_list():
            if frappe.get_cached_value("Item", d.item_code, "is_stock_item") == 1 and flt(d.qty):
                if flt(d.conversion_factor) == 0.0:
                    d.conversion_factor = (
                        get_conversion_factor(d.item_code, d.uom).get("conversion_factor") or 1.0
                    )

                # On cancellation or return entry submission, make stock ledger entry for
                # target warehouse first, to update serial no values properly

                if d.warehouse and (
                    (not cint(self.is_return) and self.docstatus == 1)
                    or (cint(self.is_return) and self.docstatus == 2)
                ):
                    sl_entries.append(self.get_sle_for_source_warehouse(d))
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")
                    print("Condition_1")

                if d.target_warehouse:
                    sl_entries.append(self.get_sle_for_target_warehouse(d))
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")
                    print("Condition_2")

                if d.warehouse and (
                    (not cint(self.is_return) and self.docstatus == 2)
                    or (cint(self.is_return) and self.docstatus == 1)
                ):
                    sl_entries.append(self.get_sle_for_source_warehouse(d))
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")
                    print("Condition_3")

        self.make_sl_entries(sl_entries)

    def get_sle_for_source_warehouse(self, item_row):
        sle = self.get_sl_entries(
            item_row,
            {
                "actual_qty": -1 * flt(item_row.qty),
                "incoming_rate": item_row.incoming_rate,
                "recalculate_rate": cint(self.is_return),
            },
        )
        if item_row.target_warehouse and not cint(self.is_return):
            sle.dependant_sle_voucher_detail_no = item_row.name

        return sle

    def get_sle_for_target_warehouse(self, item_row):
        sle = self.get_sl_entries(
            item_row, {"actual_qty": flt(item_row.qty), "warehouse": item_row.target_warehouse}
        )

        if self.docstatus == 1:
            if not cint(self.is_return):
                sle.update({"incoming_rate": item_row.incoming_rate, "recalculate_rate": 1})
            else:
                sle.update({"outgoing_rate": item_row.incoming_rate})
                if item_row.warehouse:
                    sle.dependant_sle_voucher_detail_no = item_row.name

        return sle
