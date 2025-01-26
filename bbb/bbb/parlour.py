# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import json

import frappe
from frappe.utils.nestedset import get_root_of

from erpnext.accounts.doctype.pos_invoice.pos_invoice import get_stock_availability
from erpnext.accounts.doctype.pos_profile.pos_profile import get_child_nodes, get_item_groups
from frappe.www.printview import get_html_and_style
from frappe.utils import now_datetime, nowdate, get_datetime, flt


def search_by_term(search_term, warehouse, price_list):
    result = search_for_serial_or_batch_or_barcode_number(search_term) or {}

    item_code = result.get("item_code") or search_term
    serial_no = result.get("serial_no") or ""
    batch_no = result.get("batch_no") or ""
    barcode = result.get("barcode") or ""

    if result:
        item_info = frappe.db.get_value(
            "Item",
            item_code,
            [
                "name as item_code",
                "item_name",
                "description",
                "stock_uom",
                "image as item_image",
                "is_stock_item",
                "start_date",
                "end_date",
                "discount_amount",
                "price_rule_tag"
            ],
            as_dict=1,
        )

        item_stock_qty, is_stock_item = get_stock_availability(item_code, warehouse)
        price_list_rate, currency = frappe.db.get_value(
            "Item Price",
            {"price_list": price_list, "item_code": item_code},
            ["price_list_rate", "currency"],
        ) or [None, None]
        if item_info:
            item_info.update(
                {
                    "serial_no": serial_no,
                    "batch_no": batch_no,
                    "barcode": barcode,
                    "price_list_rate": price_list_rate,
                    "currency": currency,
                    "actual_qty": item_stock_qty,
                }
            )
            return {"items": [item_info]}
        else:
            return []


@frappe.whitelist()
def get_items(start, page_length, price_list, item_group, pos_profile, search_term=""):
    warehouse, hide_unavailable_items = frappe.db.get_value(
        "POS Profile", pos_profile, ["warehouse", "hide_unavailable_items"]
    )

    result = []

    if search_term:
        result = search_by_term(search_term, warehouse, price_list) or []
        if result:
            return result

    if not frappe.db.exists("Item Group", item_group):
        item_group = get_root_of("Item Group")

    condition = get_conditions(search_term)
    condition += get_item_group_condition(pos_profile)

    lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])

    bin_join_selection, bin_join_condition = "", ""
    if hide_unavailable_items:
        bin_join_selection = ", `tabBin` bin"
        bin_join_condition = (
            "AND bin.warehouse = %(warehouse)s AND bin.item_code = item.name AND bin.actual_qty > 0"
        )

    items_data = frappe.db.sql(
        """
        SELECT
            item.name AS item_code,
            item.item_name,
            item.description,
            item.stock_uom,
            item.start_date,
            item.end_date,
            item.discount_amount,
            item.price_rule_tag,
            item.image AS item_image,
            item.is_stock_item
        FROM
            `tabItem` item {bin_join_selection}
        WHERE
            item.disabled = 0
            AND (item.company = 'Orkas Glam Bar And Revive Spa' OR item.company IS NULL OR item.company = '')
            AND item.has_variants = 0
            AND item.is_sales_item = 1
            AND item.is_fixed_asset = 0
            AND item.item_group in (SELECT name FROM `tabItem Group` WHERE lft >= {lft} AND rgt <= {rgt})
            AND {condition}
            {bin_join_condition}
        ORDER BY
            item.name asc
        LIMIT
            {start}, {page_length}""".format(
            start=start,
            page_length=page_length,
            lft=lft,
            rgt=rgt,
            condition=condition,
            bin_join_selection=bin_join_selection,
            bin_join_condition=bin_join_condition,
        ),
        {"warehouse": warehouse},
        as_dict=1,
    )

    if items_data:
        items = [d.item_code for d in items_data]
        item_prices_data = frappe.get_all(
            "Item Price",
            fields=["item_code", "price_list_rate", "currency"],
            filters={"price_list": price_list, "item_code": ["in", items]},
        )

        item_prices = {}
        for d in item_prices_data:
            item_prices[d.item_code] = d

        for item in items_data:
            item_code = item.item_code
            item_price = item_prices.get(item_code) or {}
            item_stock_qty, is_stock_item = get_stock_availability(
                item_code, warehouse)

            row = {}
            row.update(item)
            row.update(
                {
                    "price_list_rate": item_price.get("price_list_rate"),
                    "currency": item_price.get("currency"),
                    "actual_qty": item_stock_qty,
                }
            )
            result.append(row)

    return {"items": result}


@frappe.whitelist()
def search_for_serial_or_batch_or_barcode_number(search_value):
    # search barcode no
    barcode_data = frappe.db.get_value(
        "Item Barcode", {"barcode": search_value}, ["barcode", "parent as item_code"], as_dict=True
    )
    if barcode_data:
        return barcode_data

    # search serial no
    serial_no_data = frappe.db.get_value(
        "Serial No", search_value, ["name as serial_no", "item_code"], as_dict=True
    )
    if serial_no_data:
        return serial_no_data

    # search batch no
    batch_no_data = frappe.db.get_value(
        "Batch", search_value, ["name as batch_no", "item as item_code"], as_dict=True
    )
    if batch_no_data:
        return batch_no_data

    return {}


def get_conditions(search_term):
    condition = "("
    condition += """item.name like {search_term}
		or item.item_name like {search_term}""".format(
        search_term=frappe.db.escape("%" + search_term + "%")
    )
    condition += add_search_fields_condition(search_term)
    condition += ")"

    return condition


def add_search_fields_condition(search_term):
    condition = ""
    search_fields = frappe.get_all("POS Search Fields", fields=["fieldname"])
    if search_fields:
        for field in search_fields:
            condition += " or item.`{0}` like {1}".format(
                field["fieldname"], frappe.db.escape("%" + search_term + "%")
            )
    return condition


def get_item_group_condition(pos_profile):
    cond = "and 1=1"
    item_groups = get_item_groups(pos_profile)
    if item_groups:
        cond = "and item.item_group in (%s)" % (", ".join(["%s"] * len(item_groups)))

    return cond % tuple(item_groups)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def item_group_query(doctype, txt, searchfield, start, page_len, filters):
    item_groups = []
    cond = "1=1"
    pos_profile = filters.get("pos_profile")

    if pos_profile:
        item_groups = get_item_groups(pos_profile)

        if item_groups:
            cond = "name in (%s)" % (", ".join(["%s"] * len(item_groups)))
            cond = cond % tuple(item_groups)

    return frappe.db.sql(
        """ select distinct name from `tabItem Group`
            where {condition} and (company = 'Orkas Glam Bar And Revive Spa' OR company IS NULL OR company = '') and (name like %(txt)s) limit {start}, {page_len}""".format(
            condition=cond, start=start, page_len=page_len
        ),
        {"txt": "%%%s%%" % txt},
    )


@frappe.whitelist()
def check_opening_entry(user):
    open_vouchers = frappe.db.get_all(
        "POS Opening Entry",
        filters={"user": user, "pos_closing_entry": [
            "in", ["", None]], "docstatus": 1},
        fields=["name", "company", "pos_profile", "period_start_date"],
        order_by="period_start_date desc",
    )

    return open_vouchers


@frappe.whitelist()
def create_opening_voucher(pos_profile, company, balance_details):
    balance_details = json.loads(balance_details)

    new_pos_opening = frappe.get_doc(
        {
            "doctype": "POS Opening Entry",
            "period_start_date": frappe.utils.get_datetime(),
            "posting_date": frappe.utils.getdate(),
            "user": frappe.session.user,
            "pos_profile": pos_profile,
            "company": company,
        }
    )
    new_pos_opening.set("balance_details", balance_details)
    new_pos_opening.submit()

    return new_pos_opening.as_dict()


@frappe.whitelist()
def get_past_order_list(search_term, status, limit=20):
    fields = ["name", "grand_total", "currency", "customer", "posting_time", "posting_date"]
    invoice_list = []

    if search_term and status:
        invoices_by_customer = frappe.db.get_all(
            "POS Invoice",
            filters={"customer": ["like", "%{}%".format(search_term)], "status": status},
            fields=fields,
        )
        invoices_by_name = frappe.db.get_all(
            "POS Invoice",
            filters={"name": ["like", "%{}%".format(search_term)], "status": status},
            fields=fields,
        )

        invoice_list = invoices_by_customer + invoices_by_name
    elif status:
        invoice_list = frappe.db.get_all("POS Invoice", filters={"status": status}, fields=fields)

    return invoice_list


@frappe.whitelist()
def set_customer_info(fieldname, customer, value=""):
    if fieldname == "loyalty_program":
        frappe.db.set_value("Customer", customer, "loyalty_program", value)

    contact = frappe.get_cached_value("Customer", customer, "customer_primary_contact")
    if not contact:
        contact = frappe.db.sql(
            """
            SELECT parent FROM `tabDynamic Link`
            WHERE
                parenttype = 'Contact' AND
                parentfield = 'links' AND
                link_doctype = 'Customer' AND
                link_name = %s
            """,
            (customer),
            as_dict=1,
        )
        contact = contact[0].get("parent") if contact else None

    if not contact:
        new_contact = frappe.new_doc("Contact")
        new_contact.is_primary_contact = 1
        new_contact.first_name = customer
        new_contact.set("links", [{"link_doctype": "Customer", "link_name": customer}])
        new_contact.save()
        contact = new_contact.name
        frappe.db.set_value("Customer", customer, "customer_primary_contact", contact)

    contact_doc = frappe.get_doc("Contact", contact)
    if fieldname == "email_id":
        contact_doc.set("email_ids", [{"email_id": value, "is_primary": 1}])
        frappe.db.set_value("Customer", customer, "email_id", value)
    elif fieldname == "mobile_no":
        contact_doc.set("phone_nos", [{"phone": value, "is_primary_mobile_no": 1}])
        frappe.db.set_value("Customer", customer, "mobile_no", value)
    contact_doc.save()


@frappe.whitelist()
def get_pos_profile_data(pos_profile):
    pos_profile = frappe.get_doc("POS Profile", pos_profile)
    pos_profile = pos_profile.as_dict()

    _customer_groups_with_children = []
    for row in pos_profile.customer_groups:
        children = get_child_nodes("Customer Group", row.customer_group)
        _customer_groups_with_children.extend(children)

    pos_profile.customer_groups = _customer_groups_with_children
    return pos_profile

@frappe.whitelist()
def create_service_record(pos_invoice):
    pos_invoice_doc = frappe.get_doc('POS Invoice', pos_invoice)
    service_record_list = []
    for index, item in enumerate(pos_invoice_doc.items):
        qty = int(item.qty)
        for item_qty in range(1, qty+1):
            doc = frappe.get_doc({
                'doctype': 'Service Record',
                'service_code': item.item_code,
                'service_no': index + item_qty,
                'location': pos_invoice_doc.pos_profile,
                'customer': pos_invoice_doc.customer,
                'invoice_no': pos_invoice,
                'status': 'Pending For Service',
                'service_date': nowdate()

            })
            doc.insert()
            service_record_list.append(doc.name)
    return service_record_list



@frappe.whitelist()
def get_all(doctype, name, print_format, no_letterhead, letterhead, settings, lang):
    res = get_html_and_style(doc=doctype, name=name, print_format=print_format, no_letterhead=no_letterhead,
                             letterhead=letterhead, settings=settings)
    return res


@frappe.whitelist()
def get_advance_booking(pos_profile, customer=None, name=None):
    print(name)
    if customer and name:
        advance_booking_list = frappe.get_all('Advance Booking', {
                                              'pos_profile': pos_profile, 'name': name, 'customer': customer, 'status': ['!=', 'complete'], 'docstatus': 1}, ['name', 'customer', 'actual_service_date'])
    elif customer:
        advance_booking_list = frappe.get_all('Advance Booking', {
                                              'pos_profile': pos_profile, 'customer': customer, 'status': ['!=', 'complete'], 'docstatus': 1}, ['name', 'customer', 'actual_service_date'])
    elif name:
        advance_booking_list = frappe.get_all('Advance Booking', {
                                              'pos_profile': pos_profile, 'name': name, 'status': ['!=', 'complete'], 'docstatus': 1}, ['name', 'customer', 'actual_service_date'])
    else:
        advance_booking_list = []
        # advance_booking_list = frappe.get_all('Advance Booking', {'pos_profile': pos_profile}, [
        #                                       'name', 'customer', 'actual_service_date'])

    return advance_booking_list


@frappe.whitelist()
def set_advance_booking_advances(self):
    """Returns list of advances against Account, Party, Reference"""

    advance_booking_doc = frappe.get_doc(
        'Advance Booking', self.advance_booking_doc)
    self.set("advances", [])
    advance_allocated = 0
    if self.get("party_account_currency") == self.company_currency:
        amount = self.get("base_rounded_total") or self.base_grand_total
    else:
        amount = self.get("rounded_total") or self.grand_total

    allocated_amount = min(amount - advance_allocated,
                           advance_booking_doc.total_advance)
    advance_allocated += flt(allocated_amount)

    advance_row = {
        "doctype": "Sales Invoice Advance",
        "reference_type": "Advance Booking",
        "reference_name": advance_booking_doc.name,
        "remarks": 'Amount BDT {} received from {}'.format(advance_booking_doc.total_advance, advance_booking_doc.customer),
        "advance_amount": flt(advance_booking_doc.total_advance),
        "allocated_amount": flt(advance_booking_doc.total_advance),
        "ref_exchange_rate": 1
    }

    self.append("advances", advance_row)
