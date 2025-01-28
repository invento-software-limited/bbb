import frappe

def execute():
    # Define indexes to be created
    index_definitions = {
        "POS Invoice": [
            "CREATE INDEX idx_pos_invoice_optimized ON `tabPOS Invoice` (owner, docstatus, pos_profile, consolidated_invoice, posting_date, posting_time)"
        ],
        "Item Group": [
            "CREATE INDEX idx_item_group_lft_rgt ON `tabItem Group` (lft, rgt)"
        ],
        "Item": [
            "CREATE INDEX idx_item_conditions ON `tabItem` (disabled, has_variants, is_sales_item, item_group)"
        ],
        "Sales Invoice": [
            "CREATE INDEX idx_sales_invoice_pos ON `tabSales Invoice` (`pos_profile`, `posting_date`)"
        ],
        "POS Closing Entry": [
            "CREATE INDEX idx_pos_closing_entry_docstatus ON `tabPOS Closing Entry` (`docstatus`)"
        ]
    }

    # Iterate over the index definitions
    for doctype, index_queries in index_definitions.items():
        for query in index_queries:
            # Extract the index name for existence check
            index_name = query.split("ON")[0].split("INDEX")[1].strip()
            
            # Check if the index already exists
            if not frappe.db.sql(
                f"SHOW INDEX FROM `tab{doctype}` WHERE Key_name = %s", (index_name,)
            ):
                # Create the index if it doesn't exist
                frappe.db.sql(query)
