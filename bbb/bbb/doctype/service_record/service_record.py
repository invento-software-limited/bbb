# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe
from frappe.utils import today, flt, now, cstr, cint
from frappe.defaults import get_defaults
from erpnext.accounts.utils import get_fiscal_year
from erpnext.stock.stock_ledger import make_sl_entries

from erpnext.controllers.stock_controller import StockController


class ServiceRecord(Document):

    def validate(self):
        print('Called')

    def on_submit(self):
        self.update_stock_ledger(submitted=1)

    def on_cancel(self):
        self.update_stock_ledger(cancelled=1)

    def get_target_warehouse(self):
        return frappe.db.get_value('POS Profile', {'name': self.location}, ['warehouse'])

    def get_item_list(self):
        default_target_warehouse = self.get_target_warehouse()
        service_code = frappe.get_doc('Item', self.service_code)
        il = []
        for d in service_code.consumable_items:
            if d.qty is None:
                frappe.throw(_("Row {0}: Qty is mandatory").format(d.idx))
            else:
                il.append(
                    frappe._dict(
                        {
                            "warehouse": '',
                            "item_code": d.item_code,
                            "qty": d.qty,
                            "uom": d.uom,
                            "stock_uom": d.uom,
                            "conversion_factor": 1,
                            "batch_no": cstr(d.get("batch_no")).strip(),
                            "serial_no": cstr(d.get("serial_no")).strip(),
                            "name": d.name,
                            "target_warehouse": default_target_warehouse,
                            "company": self.company,
                            "voucher_type": self.doctype,
                            "allow_zero_valuation": 0,
                            "consumable_item": d.item_code,
                            "incoming_rate": 0,
                        }
                    )
                )

        return il

    def update_stock_ledger(self, submitted=False, cancelled=0):
        # self.update_reserved_qty()

        sl_entries = []
        # Loop over items and packed items table
        for d in self.get_item_list():
            # if submitted:
            sl_entries.append(self.get_sle_for_source_warehouse(d, cancelled = cancelled))
            # elif cancelled:
            #     sl_entries.append(self.get_sle_for_target_warehouse(d, cancelled = cancelled))

        make_sl_entries(sl_entries, allow_negative_stock=True)

    def get_sle_for_source_warehouse(self, item_row, cancelled):
        sle = self.get_sl_entries(
            item_row,
            {
                "actual_qty": -1 * flt(item_row.qty),
                "incoming_rate": item_row.incoming_rate,
                "recalculate_rate":cancelled,
                "is_cancelled": cancelled
        },
        )

        return sle

    def get_sle_for_target_warehouse(self, item_row, cancelled):
        sle = self.get_sl_entries(
            item_row, {"actual_qty": -1 * flt(item_row.qty), "warehouse": item_row.target_warehouse, 'is_cancelled': cancelled}
        )

        if self.docstatus == 1:
            if not cint(self.is_return):
                sle.update({"incoming_rate": item_row.incoming_rate, "recalculate_rate": 1})
            else:
                sle.update({"outgoing_rate": item_row.incoming_rate})
                if item_row.warehouse:
                    sle.dependant_sle_voucher_detail_no = item_row.name

        return sle

    def get_sl_entries(self, d, args):
        valuation_rate = frappe.db.get_value('Item', d.get('item_code'), 'valuation_rate')
        warehouse = frappe.db.get_value('POS Profile', self.location, 'warehouse')

        sl_dict = frappe._dict(
            {
                "item_code": d.get("item_code", None),
                "warehouse": warehouse,
                "posting_date": today(),
                "posting_time": frappe.utils.nowtime(),
                "fiscal_year": get_fiscal_year(today(), company=self.company)[0],
                "voucher_type": self.doctype,
                "voucher_no": self.name,
                "voucher_detail_no": d.name,
                # "actual_qty": (self.docstatus == 1 and 1 or -1) * flt(d.get("stock_qty")),
                # "actual_qty": (-1 if self.docstatus == 2 else 1) * flt(d.get("qty")),
                "stock_uom": frappe.db.get_value(
                    "Item", args.get("item_code") or d.get("item_code"), "stock_uom"
                ),
                "incoming_rate": 0,
                "valuation_rate": valuation_rate,
                "company": self.company,
                "batch_no": cstr(d.get("batch_no")).strip(),
                "serial_no": d.get("serial_no"),
                "project": d.get("project") or self.get("project"),

            }
        )
        sl_dict.update(args)
        return sl_dict
