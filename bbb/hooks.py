from . import __version__ as app_version

app_name = "bbb"
app_title = "Bbb"
app_publisher = "invento software limited"
app_description = "bbb"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "munim@invento.com.bd"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/css/custom-point-of-sale.css"
app_include_js = "/assets/js/custom-app-include-js.js"


# include js, css files in header of web template
# web_include_css = "/assets/bbb/css/bbb.css"
# web_include_js = "/assets/bbb/js/bbb.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "bbb/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {
    # "pos" : "public/js/pos_controller.js",
    # "point-of-sale": "public/js/pos_controller.js",
    "point-of-sale": "public/js/point_of_sale.js",

}

# include js in doctype views
# doctype_js = {"POS Invoice": 'public/js/point_of_sale.js'}
# doctype_list_js = {
#     "Item": "public/js/items.js"
# }
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "bbb.install.before_install"
# after_install = "bbb.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "bbb.uninstall.before_uninstall"
# after_uninstall = "bbb.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bbb.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Item": {
        "after_insert": "bbb.bbb.item.after_insert",
        "on_update": "bbb.bbb.item.on_update",
    },
    "Item Price": {
        "after_insert": "bbb.bbb.item_price_list.after_insert_or_on_update",
        "on_update": "bbb.bbb.item_price_list.after_insert_or_on_update",
    },
    # "Sales Invoice": {
    #     "before_submit": "bbb.bbb.pos_invoice.before_submit",
    # },

    "POS Invoice": {
        "after_insert": "bbb.bbb.pos_invoice.after_insert"
    },
    # "POS Invoice Merge Log": {
    #     "on_submit": "bbb.bbb.pos_invoice_merge_log.on_submit"
    # }

}
override_doctype_class = {"POS Invoice": "bbb.bbb.controllers.pos_invoice.CustomPOSInvoice"}

jenv = {
    "methods": [
        "str_to_datetime:bbb.bbb.controllers.utils.str_to_datetime",
        "get_current_datetime:bbb.bbb.controllers.utils.get_current_datetime",
        "get_invoice_total_discount_amount:bbb.bbb.controllers.utils.get_invoice_total_discount_amount",
        "get_item_total_discount_amount:bbb.bbb.controllers.utils.get_item_total_discount_amount",
        "get_invoice_before_discount_amount:bbb.bbb.controllers.utils.get_invoice_before_discount_amount",
    ]
}
# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"bbb.tasks.all"
# 	],
# 	"daily": [
# 		"bbb.tasks.daily"
# 	],
# 	"hourly": [
# 		"bbb.tasks.hourly"
# 	],
# 	"weekly": [
# 		"bbb.tasks.weekly"
# 	]
# 	"monthly": [
# 		"bbb.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "bbb.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bbb.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bbb.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {
        "doctype": "{doctype_4}"
    }
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"bbb.auth.validate"
# ]
