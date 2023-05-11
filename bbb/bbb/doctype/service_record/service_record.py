# Copyright (c) 2023, invento software limited and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ServiceRecord(Document):
    def validate(self):
        print('Called')
    def on_submit(self):
        pass

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
                if d.warehouse:
                    sl_entries.append(self.get_sle_for_source_warehouse(d))
                elif d.target_warehouse:
                    sl_entries.append(self.get_sle_for_target_warehouse(d))

        self.make_sl_entries(sl_entries)

    def get_sle_for_source_warehouse(self, item_row):
        self.is_return = 1 if self.docstatus == 1 else 0
        sle = self.get_sl_entries(
            item_row,
            {
                "actual_qty": -1 * flt(item_row.qty),
                "incoming_rate": item_row.incoming_rate,
                "recalculate_rate": cint(self.is_return),
            },
        )
        # if item_row.target_warehouse and not cint(self.is_return):
        #     sle.dependant_sle_voucher_detail_no = item_row.name

        return sle

    def get_sle_for_target_warehouse(self, item_row):
        self.is_return = 1 if self.docstatus == 2 else 0
        sle = self.get_sl_entries(
            item_row, {"actual_qty": flt(item_row.qty), "warehouse": item_row.target_warehouse}
        )
        return sle

    def get_sl_entries(self, d, args):
        valuation_rate = frappe.db.get_value('Item', d.get('item_code'), 'valuation_rate')

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
                "valuation_rate": valuation_rate,
                "company": self.company,
                "batch_no": cstr(d.get("batch_no")).strip(),
                "serial_no": d.get("serial_no"),
                "project": d.get("project") or self.get("project"),
                "is_cancelled": 1 if self.docstatus == 2 else 0,
            }
        )
        sl_dict.update(args)
        return sl_dict
