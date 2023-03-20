# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json

import frappe
import frappe.utils
from frappe import _
from frappe.contacts.doctype.address.address import get_company_address
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
from frappe.utils import add_days, cint, cstr, flt, get_link_to_form, getdate, nowdate, strip_html
from six import string_types

from erpnext.accounts.doctype.sales_invoice.sales_invoice import (
    unlink_inter_company_doc,
    update_linked_doc,
    validate_inter_company_party,
)
from erpnext.controllers.selling_controller import SellingController
from erpnext.manufacturing.doctype.production_plan.production_plan import (
    get_items_for_material_requests,
)
from erpnext.selling.doctype.customer.customer import check_credit_limit
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.stock.doctype.item.item import get_item_defaults
from erpnext.stock.stock_balance import get_reserved_qty, update_bin_qty

import erpnext
from erpnext.accounts.general_ledger import (
    make_gl_entries,
    make_reverse_gl_entries,
    process_gl_map,
)
from erpnext.accounts.utils import get_fiscal_year

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}
from erpnext.selling.doctype.sales_order.sales_order import SalesOrder


class WarehouseRequired(frappe.ValidationError):
    pass


class CustomSalesOrder(SalesOrder):
    def __init__(self, *args, **kwargs):
        super(CustomSalesOrder, self).__init__(*args, **kwargs)

    def on_submit(self):
        super(CustomSalesOrder, self).on_submit()
        self.update_stock_ledger()

    def on_cancel(self):
        super(CustomSalesOrder, self).on_cancel()
        self.update_stock_ledger()

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
                                    "warehouse": 'Distribution - BBB',
                                    "item_code": p.item_code,
                                    "qty": flt(p.qty),
                                    "uom": p.uom,
                                    "batch_no": cstr(p.batch_no).strip(),
                                    "serial_no": cstr(p.serial_no).strip(),
                                    "name": d.name,
                                    "target_warehouse": 'Distribution - BBB',
                                    "company": self.company,
                                    "voucher_type": self.doctype,
                                    "allow_zero_valuation": 0,
                                    "sales_order_item": d.get("sales_order_item"),
                                    "dn_detail": d.get("dn_detail"),
                                    "incoming_rate": p.get("incoming_rate"),
                                }
                            )
                        )
            else:
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
                            "target_warehouse": 'Distribution - BBB',
                            "company": self.company,
                            "voucher_type": self.doctype,
                            "allow_zero_valuation": 0,
                            "sales_order_item": d.get("sales_order_item"),
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

                sl_entries.append(self.get_sle_for_source_warehouse(d))

        self.make_sl_entries(sl_entries)

    def get_sle_for_source_warehouse(self, item_row):
        if self.docstatus == 2:
            self.is_return = 1

        sle = self.get_sl_entries(
            item_row,
            {
                "actual_qty": 1 * flt(item_row.qty),
                "incoming_rate": item_row.incoming_rate,
                # "recalculate_rate": cint(self.is_return),
                "recalculate_rate": 1 if self.docstatus == 2 else 0,
            },
        )
        # if item_row.target_warehouse and not cint(self.is_return):
        #     sle.dependant_sle_voucher_detail_no = item_row.name
        if item_row.target_warehouse and self.docstatus == 1:
            sle.dependant_sle_voucher_detail_no = item_row.name

        return sle

    # def update_stock_ledger(self):
    # 	sl_entries = []
    # 	finished_item_row = self.get_finished_item_row()

    # 	# make sl entries for source warehouse first
    # 	self.get_sle_for_source_warehouse(sl_entries, finished_item_row)

    # 	# SLE for target warehouse
    # 	self.get_sle_for_target_warehouse(sl_entries, finished_item_row)

    # 	# reverse sl entries if cancel
    # 	if self.docstatus == 2:
    # 		sl_entries.reverse()

    # 	self.make_sl_entries(sl_entries)

    # def get_sle_for_source_warehouse(self, item_row):
    # 	sle = self.get_sl_entries(
    # 		item_row,
    # 		{
    # 			"actual_qty": -1 * flt(item_row.qty),
    # 			"incoming_rate": item_row.incoming_rate,
    # 			"recalculate_rate": cint(self.is_return),
    # 		},
    # 	)
    # 	if item_row.target_warehouse and not cint(self.is_return):
    # 		sle.dependant_sle_voucher_detail_no = item_row.name

    # 	return sle

    # def get_sle_for_target_warehouse(self, item_row):
    # 	sle = self.get_sl_entries(
    # 		item_row, {"actual_qty": flt(item_row.qty), "warehouse": item_row.target_warehouse}
    # 	)

    # 	if self.docstatus == 1:
    # 		if not cint(self.is_return):
    # 			sle.update({"incoming_rate": item_row.incoming_rate, "recalculate_rate": 1})
    # 		else:
    # 			sle.update({"outgoing_rate": item_row.incoming_rate})
    # 			if item_row.warehouse:
    # 				sle.dependant_sle_voucher_detail_no = item_row.name

    # 	return sle

    def get_sl_entries(self, d, args):
        sl_dict = frappe._dict(
            {
                "item_code": d.get("item_code", None),
                "warehouse": d.get("warehouse", None),
                "posting_date": self.transaction_date,
                "posting_time": frappe.utils.nowtime(),
                "fiscal_year": get_fiscal_year(self.transaction_date, company=self.company)[0],
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "voucher_detail_no": d.name,
                # "actual_qty": (self.docstatus == 1 and 1 or -1) * flt(d.get("stock_qty")),
                "actual_qty": (-1 if self.docstatus == 2 else 1) * flt(d.get("stock_qty")),
                "stock_uom": frappe.db.get_value(
                    "Item", args.get("item_code") or d.get("item_code"), "stock_uom"
                ),
                "incoming_rate": 0,
                "valuation_rate": d.get('valuation_rate'),
                "company": self.company,
                "batch_no": cstr(d.get("batch_no")).strip(),
                "serial_no": d.get("serial_no"),
                "project": d.get("project") or self.get("project"),
                "is_cancelled": 1 if self.docstatus == 2 else 0,
            }
        )

        sl_dict.update(args)
        return sl_dict

