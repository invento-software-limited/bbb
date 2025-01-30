import frappe

def execute():
    index_definitions = {
        "Customer": [
            ("idx_customer_name", "name, customer_group, territory"),
            ("idx_customer_search", "customer_name")
        ]
    }

    for doctype, indexes in index_definitions.items():
        for index_name, columns in indexes:
            # Check if the index already exists
            existing_index = frappe.db.sql(
                f"SHOW INDEX FROM `tab{doctype}` WHERE Key_name = %s", (index_name,)
            )
            if not existing_index:
                # Create the index if it doesn't exist
                frappe.db.sql(f"CREATE INDEX {index_name} ON `tab{doctype}` ({columns});")
