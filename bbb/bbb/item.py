import frappe
from frappe import _


def validate(doc, method):
    if doc.is_service:
        total_weight = 0.0
        try:
            total_weight += float(doc.service_person_1) if doc.service_person_1 else 0.0
        except:
            frappe.throw(_("Service person 1 weight should be a number"))

        try:
            total_weight += float(doc.service_person_2) if doc.service_person_2 else 0.0
        except:
            frappe.throw(_("Service person 2 weight should be a number"))

        try:
            total_weight += float(doc.service_person_3) if doc.service_person_3 else 0.0
        except:
            frappe.throw(_("Service person 3 weight should be a number"))

        try:
            total_weight += float(doc.service_person_4) if doc.service_person_4 else 0.0
        except:
            frappe.throw(_("Service person 4 weight should be a number"))

        if total_weight != 100:
            frappe.throw(_("Service person total weight should be 100"))


def after_insert(doc, method):
    # For Standard Selling
    if doc.standard_rate is None or doc.standard_rate == 0:
        item_price = frappe.new_doc('Item Price')
        item_price.item_code = doc.item_code
        item_price.price_list_rate = 0
        item_price.price_list = 'Standard Selling'
        item_price.selling = 1
        item_price.save()

    # For Standard Buying
    item_price = frappe.new_doc('Item Price')
    item_price.item_code = doc.item_code
    item_price.price_list_rate = doc.buying_rate if doc.buying_rate else 0
    item_price.price_list = 'Standard Buying'
    item_price.buying = 1
    item_price.save()


def on_update(doc, method):
    selling_price = frappe.get_doc('Item Price', {'item_code': doc.item_code, 'selling': 1})
    buying_price = frappe.get_doc('Item Price', {'item_code': doc.item_code, 'buying': 1})

    # For selling price
    selling_price.price_list_rate = doc.standard_rate if doc.standard_rate else 0
    selling_price.save()

    # For buying price
    buying_price.price_list_rate = doc.buying_rate if doc.buying_rate else 0
    buying_price.save()
