# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.contacts.doctype.address.address import get_company_address
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.model.utils import get_fetch_values
# from frappe.utils import cint, flt
from frappe.utils import cint, cstr, flt, get_link_to_form, getdate

from erpnext.controllers.accounts_controller import get_taxes_and_charges
from erpnext.controllers.selling_controller import SellingController
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.stock.doctype.serial_no.serial_no import get_delivery_note_serial_no
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}


class CustomDeliveryNote(DeliveryNote):
    def __init__(self, *args, **kwargs):
        super(CustomDeliveryNote, self).__init__(*args, **kwargs)
        self.status_updater = [
            {
                "source_dt": "Delivery Note Item",
                "target_dt": "Sales Order Item",
                "join_field": "so_detail",
                "target_field": "delivered_qty",
                "target_parent_dt": "Sales Order",
                "target_parent_field": "per_delivered",
                "target_ref_field": "qty",
                "source_field": "qty",
                "percent_join_field": "against_sales_order",
                "status_field": "delivery_status",
                "keyword": "Delivered",
                "second_source_dt": "Sales Invoice Item",
                "second_source_field": "qty",
                "second_join_field": "so_detail",
                "overflow_type": "delivery",
                "second_source_extra_cond": """ and exists(select name from `tabSales Invoice`
        		where name=`tabSales Invoice Item`.parent and update_stock = 1)""",
            },
            {
                "source_dt": "Delivery Note Item",
                "target_dt": "Sales Invoice Item",
                "join_field": "si_detail",
                "target_field": "delivered_qty",
                "target_parent_dt": "Sales Invoice",
                "target_ref_field": "qty",
                "source_field": "qty",
                "percent_join_field": "against_sales_invoice",
                "overflow_type": "delivery",
                "no_allowance": 1,
            },
        ]
        if cint(self.is_return):
            self.status_updater.extend(
                [
                    {
                        "source_dt": "Delivery Note Item",
                        "target_dt": "Sales Order Item",
                        "join_field": "so_detail",
                        "target_field": "returned_qty",
                        "target_parent_dt": "Sales Order",
                        "source_field": "-1 * qty",
                        "second_source_dt": "Sales Invoice Item",
                        "second_source_field": "-1 * qty",
                        "second_join_field": "so_detail",
                        "extra_cond": """ and exists (select name from `tabDelivery Note`
        			where name=`tabDelivery Note Item`.parent and is_return=1)""",
                        "second_source_extra_cond": """ and exists (select name from `tabSales Invoice`
        			where name=`tabSales Invoice Item`.parent and is_return=1 and update_stock=1)""",
                    },
                    {
                        "source_dt": "Delivery Note Item",
                        "target_dt": "Delivery Note Item",
                        "join_field": "dn_detail",
                        "target_field": "returned_qty",
                        "target_parent_dt": "Delivery Note",
                        "target_parent_field": "per_returned",
                        "target_ref_field": "stock_qty",
                        "source_field": "-1 * stock_qty",
                        "percent_join_field_parent": "return_against",
                    },
                ]
            )
    def get_default_distribution_warehouse(self):
        company_doc = frappe.get_doc('Company', {'name': self.company})
        default_source_warehouse = company_doc.default_source_warehouse_for_distribution
        default_target_warehouse = company_doc.default_target_warehouse_for_distribution
        return default_source_warehouse, default_target_warehouse
    def get_item_list(self):
        default_source_warehouse, default_target_warehouse = self.get_default_distribution_warehouse()
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
                                        "warehouse": default_target_warehouse,
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
                                "warehouse": default_target_warehouse,
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
        return il
