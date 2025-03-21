# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import copy

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate


def execute(filters=None):
    if not filters:
        return [], [], None, []
    filters['group_by_so'] = 1
    validate_filters(filters)

    columns = get_columns(filters)
    conditions = get_conditions(filters)
    data = get_data(conditions, filters)

    if not data:
        return [], [], None, []

    data, chart_data = prepare_data(data, filters)

    return columns, data, None


def validate_filters(filters):
    from_date, to_date = filters.get("from_date"), filters.get("to_date")

    if not from_date and to_date:
        frappe.throw(_("From and To Dates are required."))
    elif date_diff(to_date, from_date) < 0:
        frappe.throw(_("To Date cannot be before From Date."))


def get_conditions(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " and so.transaction_date between %(from_date)s and %(to_date)s"

    if filters.get("company"):
        conditions += " and so.company = %(company)s"

    if filters.get("sales_order"):
        conditions += " and so.name in %(sales_order)s"

    if filters.get("status"):
        conditions += " and so.status in %(status)s"

    return conditions


def get_data(conditions, filters):
    data = frappe.db.sql(
        """
        SELECT
            so.transaction_date as date,
            soi.delivery_date as delivery_date,
            so.name as sales_order,
            so.status, so.customer, soi.item_code,
            DATEDIFF(CURDATE(), soi.delivery_date) as delay_days,
            IF(so.status in ('Completed','To Bill'), 0, (SELECT delay_days)) as delay,
            soi.qty, soi.delivered_qty,
            (soi.qty - soi.delivered_qty) AS pending_qty,
            IFNULL(SUM(sii.qty), 0) as billed_qty,
            soi.base_amount as amount,
            (soi.delivered_qty * soi.base_rate) as delivered_qty_amount,
            (soi.billed_amt * IFNULL(so.conversion_rate, 1)) as billed_amount,
            (soi.base_amount - (soi.billed_amt * IFNULL(so.conversion_rate, 1))) as pending_amount,
            soi.warehouse as warehouse, so.advance_paid,
            so.company, soi.name, sii.parent as invoice_no, dni.parent as delivery_note,
            soi.description as description
        FROM
            `tabSales Order` so,
            `tabSales Order Item` soi
        LEFT JOIN `tabSales Invoice Item` sii
            ON sii.so_detail = soi.name and sii.docstatus = 1
        LEFT JOIN `tabDelivery Note Item` dni
            ON dni.against_sales_order = soi.parent and dni.docstatus = 1
        WHERE
            soi.parent = so.name
            and so.status not in ('Stopped', 'Closed', 'On Hold')
            and so.docstatus = 1
            {conditions}
        GROUP BY soi.name
        ORDER BY so.transaction_date ASC, soi.item_code ASC
    """.format(
            conditions=conditions
        ),
        filters,
        as_dict=1,
    )

    return data


def prepare_data(data, filters):
    completed, pending = 0, 0

    if filters.get("group_by_so"):
        sales_order_map = {}

    for row in data:
        # sum data for chart
        completed += row["billed_amount"]
        pending += row["pending_amount"]

        # prepare data for report view
        row["qty_to_bill"] = flt(row["qty"]) - flt(row["billed_qty"])
        row["delay"] = 0 if row["delay"] and row["delay"] < 0 else row["delay"]
        update_status(row)

        if filters.get("group_by_so"):
            so_name = row["sales_order"]

            if not so_name in sales_order_map:
                # create an entry
                row_copy = copy.deepcopy(row)
                sales_order_map[so_name] = row_copy
            else:
                # update existing entry
                so_row = sales_order_map[so_name]
                so_row["required_date"] = max(getdate(so_row["delivery_date"]), getdate(row["delivery_date"]))
                so_row["delay"] = min(so_row["delay"], row["delay"])

                # sum numeric columns
                fields = [
                    "qty",
                    "delivered_qty",
                    "pending_qty",
                    "billed_qty",
                    "qty_to_bill",
                    "amount",
                    "delivered_qty_amount",
                    "billed_amount",
                    "pending_amount",
                ]
                for field in fields:
                    so_row[field] = flt(row[field]) + flt(so_row[field])



    chart_data = prepare_chart_data(pending, completed)

    if filters.get("group_by_so"):
        data = []
        for so in sales_order_map:
            data.append(sales_order_map[so])
        return data, chart_data

    return data, chart_data

def update_status(row):
    if not row.get('invoice_no', None):
        row['invoice_status'] = "Not Invoiced"
    elif row['billed_qty'] > 0 and row['billed_qty'] != row['qty']:
        row['invoice_status'] = "Partly Invoiced"
    else:
        row['invoice_status'] = "Fully Invoiced"

    if row['delivered_qty'] == row['qty']:
        row['delivery_status'] = "Fully Delivered"
    elif row['delivered_qty'] < row['qty'] and row['delivered_qty'] != 0:
        row['delivery_status'] = "Partly Delivered"
    else:
        row['delivery_status'] = "Not Delivered"

    if row['pending_amount'] == 0 and row['billed_amount'] != 0:
        row['payment_status'] = "Fully Paid"
    elif row['pending_amount'] > 0 and row['billed_amount'] != 0 and row['billed_amount'] != row['amount']:
        row['payment_status'] = "Partly Paid"
    else:
        row['payment_status'] = "Unpaid"


def prepare_chart_data(pending, completed):
    labels = ["Amount to Bill", "Billed Amount"]

    return {
        "data": {"labels": labels, "datasets": [{"values": [pending, completed]}]},
        "type": "donut",
        "height": 300,
    }


def get_columns(filters):
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 90},
        {
            "label": _("Sales Order"),
            "fieldname": "sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "width": 160,
        },
        # {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 130},
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 130,
        },
    ]

    if not filters.get("group_by_so"):
        columns.append(
            {
                "label": _("Item Code"),
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 140,
            }
        )
        # columns.append(
        # 	{"label": _("Description"), "fieldname": "description", "fieldtype": "Small Text", "width": 100}
        # )

    columns.extend(
        [
            {
                "label": _("Order Qty"),
                "fieldname": "qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Delivered Qty"),
                "fieldname": "delivered_qty",
                "fieldtype": "Float",
                "width": 120,
                "convertible": "qty",
            },
            {
                "label": _("Amount"),
                "fieldname": "amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Billed Amount"),
                "fieldname": "billed_amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },
            {
                "label": _("Advance Paid"),
                "fieldname": "advance_paid",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },

            {
                "label": _("Invoice Status"),
                "fieldname": "invoice_status",
                "fieldtype": "Text",
                "width": 130,
            },
            {
                "label": _("Invoice No"),
                "fieldname": "invoice_no",
                "fieldtype": "Link",
                "width": 130,
                "options": "Sales Invoice",
            },

            {
                "label": _("Delivery Status"),
                "fieldname": "delivery_status",
                "fieldtype": "Text",
                "width": 130,
            },
            {
                "label": _("Delivery No"),
                "fieldname": "delivery_note",
                "fieldtype": "Link",
                "width": 130,
                "options": "Delivery Note",
            },

            {
                "label": _("Payment Status"),
                "fieldname": "payment_status",
                "fieldtype": "Text",
                "width": 130,
            },
            {
                "label": _("Total Paid"),
                "fieldname": "billed_amount",
                "fieldtype": "Currency",
                "width": 110,
                "options": "Company:company:default_currency",
                "convertible": "rate",
            },

            # {
            # 	"label": _("Pending Amount"),
            # 	"fieldname": "pending_amount",
            # 	"fieldtype": "Currency",
            # 	"width": 130,
            # 	"options": "Company:company:default_currency",
            # 	"convertible": "rate",
            # },
            # {
            # 	"label": _("Amount Delivered"),
            # 	"fieldname": "delivered_qty_amount",
            # 	"fieldtype": "Currency",
            # 	"width": 140,
            # 	"options": "Company:company:default_currency",
            # 	"convertible": "rate",
            # },
            # {
            # 	"label": _("Qty to Deliver"),
            # 	"fieldname": "pending_qty",
            # 	"fieldtype": "Float",
            # 	"width": 120,
            # 	"convertible": "qty",
            # },
            # {
            # 	"label": _("Billed Qty"),
            # 	"fieldname": "billed_qty",
            # 	"fieldtype": "Float",
            # 	"width": 80,
            # 	"convertible": "qty",
            # },
            # {
            # 	"label": _("Qty to Bill"),
            # 	"fieldname": "qty_to_bill",
            # 	"fieldtype": "Float",
            # 	"width": 80,
            # 	"convertible": "qty",
            # },
            # {"label": _("Delivery Date"), "fieldname": "delivery_date", "fieldtype": "Date", "width": 120},
            # {"label": _("Delay (in Days)"), "fieldname": "delay", "fieldtype": "Data", "width": 100},
        ]
    )
    if not filters.get("group_by_so"):
        # columns.append(
        #     {
        #         "label": _("Invoice No"),
        #         "fieldname": "invoice_no",
        #         "fieldtype": "Link",
        #         "width": 130,
        #         "options": "Sales Invoice",
        #     },
        # )
        columns.append(
            {
                "label": _("Warehouse"),
                "fieldname": "warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 100,
            }
        )

    columns.append(
        {
            "label": _("Company"),
            "fieldname": "company",
            "fieldtype": "Link",
            "options": "Company",
            "width": 100,
        }
    )

    return columns
