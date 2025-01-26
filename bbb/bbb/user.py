import frappe

def validate(doc, method):
    user_permission = frappe.db.exists("User Permission", {'user': doc.email, 'allow': 'Company'})
    if user_permission:
        permission_doc = frappe.get_doc("User Permission", user_permission)
        if doc.company and doc.company != permission_doc.for_value:
            permission_doc = frappe.get_doc("User Permission", user_permission)
            permission_doc.for_value = doc.company
            permission_doc.save()
        else:
            permission_doc.delete()
    # elif doc.company:
    #     new_doc = frappe.new_doc('User Permission')
    #     new_doc.user = doc.email
    #     new_doc.allow = 'Company'
    #     new_doc.for_value = doc.company
    #     new_doc.insert()
    #     new_doc.save()

    print(user_permission)

