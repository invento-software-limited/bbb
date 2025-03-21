# Copyright (c) 2022, invento software limited and contributors
# For license information, please see license.txt

from operator import itemgetter

import frappe
from frappe import _
from frappe.utils import cint, date_diff, flt, getdate
from six import iteritems

import erpnext
from erpnext.stock.report.stock_ageing.stock_ageing import FIFOSlots, get_average_age
from erpnext.stock.report.stock_ledger.stock_ledger import get_item_group_condition
from erpnext.stock.utils import add_additional_uom_columns, is_reposting_item_valuation_in_progress


def execute(filters=None):
    is_reposting_item_valuation_in_progress()
    if not filters:
        filters = {}
    if not filters.get('from_date'):
        return [], []

    if filters.get('from_date'):
        filters.update({'to_date': filters.get('from_date')})

    if not filters.get('all_warehouse') and not filters.get('warehouse'):
        return [], []

    from_date = filters.get("from_date")
    # to_date = filters.get("to_date")

    if filters.get("company"):
        company_currency = erpnext.get_company_currency(filters.get("company"))
    else:
        company_currency = frappe.db.get_single_value("Global Defaults", "default_currency")

    include_uom = filters.get("include_uom")
    columns = get_columns(filters)
    items = get_items(filters)
    sle = get_stock_ledger_entries(filters, items, columns)

    # if filters.get("show_stock_ageing_data"):
    #     filters["show_warehouse_wise_stock"] = True
    #     item_wise_fifo_queue = FIFOSlots(filters, sle).generate()

    # if no stock ledger entry found return
    if not sle:
        return columns, []

    iwb_map = get_item_warehouse_map(filters, sle)
    item_map = get_item_details(items, sle, filters)
    item_reorder_detail_map = get_item_reorder_details(item_map.keys())



    data = []
    conversion_factors = {}

    _func = itemgetter(1)

    if filters.get('all_warehouse'):
        all_warehouse = frappe.db.get_list('Warehouse', {'company': filters.get('company')}, 'name')
        warehouse_list = [wh.name for wh in all_warehouse]
    elif filters.get("warehouse"):
        warehouse_list = filters.get('warehouse')

    for (company, item, warehouse) in sorted(iwb_map):
        if item_map.get(item):
            qty_dict = iwb_map[(company, item, warehouse)]
            report_data = {
                "currency": company_currency,
                "item_code": item,
                "company": company,
            }
            item_code = item
            index = next(
                (index for (index, d) in enumerate(data) if d['item_code'] == item_code), None)

            report_data.update(item_map[item])
            if index is not None:
                standard_rate = data[index]['standard_rate']

                data[index]['bal_qty'] = float(data[index]['bal_qty']) + qty_dict['bal_qty']
                data[index]['total_value'] = data[index]['total_value'] +  (standard_rate * qty_dict['bal_qty'])
                data[index][warehouse] = qty_dict['bal_qty']
            else:
                for wh in warehouse_list:
                    try:
                        report_data[wh] = '0'
                    except:
                        report_data[wh.warehouse_name] = '0'


                report_data.update(qty_dict)
                report_data[warehouse] = qty_dict['bal_qty']
                report_data['total_value'] = report_data['standard_rate'] * qty_dict['bal_qty']
                data.append(report_data)
    # add_additional_uom_columns(columns, data, include_uom, conversion_factors)

    return columns, data


def get_columns(filters):
    """return columns"""
    columns = [
        {
            "label": _("Product Code"),
            "fieldname": "item_code",
            "options": "Item",
            "width": 180,
        },
        {"label": _("Product Name"), "fieldname": "item_name", "width": 800},
        {
            "label": _("Total Qty"),
            "fieldname": "bal_qty",
            "fieldtype": "Float",
            "width": 100,
            "convertible": "qty",
        },
        {
            "label": _("MRP"),
            "fieldname": "standard_rate",
            "fieldtype": "Currency",
            "width": 100,
            "options": "currency",
        },
        {
            "label": _("Total Value"),
            "fieldname": "total_value",
            "fieldtype": "Currency",
            "width": 100,
            "options": "currency",
        },
    ]

    return columns


def get_conditions(filters, columns):
    conditions = ""
    if not filters.get("from_date"):
        frappe.throw(_("'From Date' is required"))

    if filters.get("to_date"):
        conditions += " and sle.posting_date <= %s" % frappe.db.escape(filters.get("to_date"))
    # else:
    #     frappe.throw(_("'To Date' is required"))

    if filters.get("company"):
        conditions += " and sle.company = %s" % frappe.db.escape(filters.get("company"))
    if filters.get('all_warehouse'):
        all_warehouse = frappe.db.get_list('Warehouse', {'company': filters.get('company')}, 'name')
        warehouse_list = [wh.name for wh in all_warehouse]
        warehouse_condition_list = []
        for warehouse in warehouse_list:
            if warehouse == 'All Warehouses - BBB':
                continue
            warehouse_details = frappe.db.get_value(
                "Warehouse", warehouse, ["lft", "rgt"], as_dict=1
            )
            if warehouse_details:
                warehouse_condition_list.append(" exists (select name from `tabWarehouse` wh \
                    where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)"
                    % (warehouse_details.lft, warehouse_details.rgt))

                columns.append({"label": _(warehouse), "fieldname": warehouse, "fieldtype": "Link", "width": 120,
                                "options": "Warehouse"}, )

        warehouse_conditions = " or ".join(warehouse_condition_list)
        conditions+=(" and (" + warehouse_conditions + ")")

    elif filters.get("warehouse"):
        warehouse_list = filters.get('warehouse')
        warehouse_condition_list = []
        for warehouse in warehouse_list:
            warehouse_details = frappe.db.get_value(
                "Warehouse", warehouse, ["lft", "rgt"], as_dict=1
            )
            if warehouse_details:
                warehouse_condition_list.append(" exists (select name from `tabWarehouse` wh \
                    where wh.lft >= %s and wh.rgt <= %s and sle.warehouse = wh.name)"
                    % (warehouse_details.lft, warehouse_details.rgt))

                columns.append({"label": _(warehouse), "fieldname": warehouse, "fieldtype": "Link", "width": 120,
                                "options": "Warehouse"}, )

        warehouse_conditions = " or ".join(warehouse_condition_list)
        conditions+=(" and (" + warehouse_conditions + ")")

    return conditions


def get_stock_ledger_entries(filters, items, columns):
	item_conditions_sql = ""
	if items:
		item_conditions_sql = " and sle.item_code in ({})".format(
			", ".join(frappe.db.escape(i, percent=False) for i in items)
		)

	conditions = get_conditions(filters, columns)

	return frappe.db.sql(
		"""
		select
			sle.item_code, warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
			sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference,
			sle.item_code as name, sle.voucher_no, sle.stock_value, sle.batch_no
		from
			`tabStock Ledger Entry` sle
		where sle.docstatus < 2 %s %s
		and is_cancelled = 0
		order by sle.posting_date, sle.posting_time, sle.creation, sle.actual_qty"""
		% (item_conditions_sql, conditions),  # nosec
		as_dict=1,
	)


def get_item_warehouse_map(filters, sle):
	iwb_map = {}
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))

	float_precision = cint(frappe.db.get_default("float_precision")) or 3

	for d in sle:
		key = (d.company, d.item_code, d.warehouse)
		if key not in iwb_map:
			iwb_map[key] = frappe._dict(
				{
					"opening_qty": 0.0,
					"opening_val": 0.0,
					"in_qty": 0.0,
					"in_val": 0.0,
					"out_qty": 0.0,
					"out_val": 0.0,
					"bal_qty": 0.0,
					"bal_val": 0.0,
					"val_rate": 0.0,
				}
			)

		qty_dict = iwb_map[(d.company, d.item_code, d.warehouse)]

		if d.voucher_type == "Stock Reconciliation" and not d.batch_no:
			qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
		else:
			qty_diff = flt(d.actual_qty)

		value_diff = flt(d.stock_value_difference)

		if d.posting_date < from_date or (
			d.posting_date == from_date
			and d.voucher_type == "Stock Reconciliation"
			and frappe.db.get_value("Stock Reconciliation", d.voucher_no, "purpose") == "Opening Stock"
		):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff

		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(qty_diff, float_precision) >= 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)

		qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff
		qty_dict.bal_val += value_diff

	iwb_map = filter_items_with_no_transactions(iwb_map, float_precision)

	return iwb_map


def filter_items_with_no_transactions(iwb_map, float_precision):
	for (company, item, warehouse) in sorted(iwb_map):
		qty_dict = iwb_map[(company, item, warehouse)]

		no_transactions = True
		for key, val in iteritems(qty_dict):
			val = flt(val, float_precision)
			qty_dict[key] = val
			if key != "val_rate" and val:
				no_transactions = False

		if no_transactions:
			iwb_map.pop((company, item, warehouse))

	return iwb_map


def get_items(filters):
	"Get items based on item code, item group or brand."
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))
		if filters.get("brand"):  # used in stock analytics report
			conditions.append("item.brand=%(brand)s")

	items = []
	if conditions:
		items = frappe.db.sql_list(
			"""select name from `tabItem` item where {}""".format(" and ".join(conditions)), filters
		)
	return items


def get_item_details(items, sle, filters):
	item_details = {}
	if not items:
		items = list(set(d.item_code for d in sle))

	if not items:
		return item_details

	cf_field = cf_join = ""
	if filters.get("include_uom"):
		cf_field = ", ucd.conversion_factor"
		cf_join = (
			"left join `tabUOM Conversion Detail` ucd on ucd.parent=item.name and ucd.uom=%s"
			% frappe.db.escape(filters.get("include_uom"))
		)

	res = frappe.db.sql(
		"""
		select
			item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom, item.standard_rate %s
		from
			`tabItem` item
			%s
		where
			item.name in (%s)
	"""
		% (cf_field, cf_join, ",".join(["%s"] * len(items))),
		items,
		as_dict=1,
	)

	for item in res:
		item_details.setdefault(item.name, item)

	if filters.get("show_variant_attributes", 0) == 1:
		variant_values = get_variant_values_for(list(item_details))
		item_details = {k: v.update(variant_values.get(k, {})) for k, v in iteritems(item_details)}

	return item_details


def get_item_reorder_details(items):
	item_reorder_details = frappe._dict()

	if items:
		item_reorder_details = frappe.db.sql(
			"""
			select parent, warehouse, warehouse_reorder_qty, warehouse_reorder_level
			from `tabItem Reorder`
			where parent in ({0})
		""".format(
				", ".join(frappe.db.escape(i, percent=False) for i in items)
			),
			as_dict=1,
		)

	return dict((d.parent + d.warehouse, d) for d in item_reorder_details)


def get_variants_attributes():
	"""Return all item variant attributes."""
	return [i.name for i in frappe.get_all("Item Attribute")]


def get_variant_values_for(items):
	"""Returns variant values for items."""
	attribute_map = {}
	for attr in frappe.db.sql(
		"""select parent, attribute, attribute_value
		from `tabItem Variant Attribute` where parent in (%s)
		"""
		% ", ".join(["%s"] * len(items)),
		tuple(items),
		as_dict=1,
	):
		attribute_map.setdefault(attr["parent"], {})
		attribute_map[attr["parent"]].update({attr["attribute"]: attr["attribute_value"]})

	return attribute_map
