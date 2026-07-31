app_name = "apil_mobile"
app_title = "APIL Mobile"
app_publisher = "Alu Products Industries Ltd"
app_description = "Mobile app integration (device registration, push notifications, approval workflow) for Alu Products Industries Ltd"
app_email = "admin@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "apil_mobile",
# 		"logo": "/assets/apil_mobile/logo.png",
# 		"title": "APIL Mobile",
# 		"route": "/apil_mobile",
# 		"has_permission": "apil_mobile.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/apil_mobile/css/apil_mobile.css"
# app_include_js = "/assets/apil_mobile/js/apil_mobile.js"

# include js, css files in header of web template
# web_include_css = "/assets/apil_mobile/css/apil_mobile.css"
# web_include_js = "/assets/apil_mobile/js/apil_mobile.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "apil_mobile/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "apil_mobile/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "apil_mobile.utils.jinja_methods",
# 	"filters": "apil_mobile.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "apil_mobile.install.before_install"
# after_install = "apil_mobile.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "apil_mobile.uninstall.before_uninstall"
# after_uninstall = "apil_mobile.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "apil_mobile.utils.before_app_install"
# after_app_install = "apil_mobile.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "apil_mobile.utils.before_app_uninstall"
# after_app_uninstall = "apil_mobile.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "apil_mobile.notifications.get_notification_config"

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

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"apil_mobile.tasks.all"
# 	],
# 	"daily": [
# 		"apil_mobile.tasks.daily"
# 	],
# 	"hourly": [
# 		"apil_mobile.tasks.hourly"
# 	],
# 	"weekly": [
# 		"apil_mobile.tasks.weekly"
# 	],
# 	"monthly": [
# 		"apil_mobile.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "apil_mobile.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "apil_mobile.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "apil_mobile.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["apil_mobile.utils.before_request"]
# after_request = ["apil_mobile.utils.after_request"]

# Job Events
# ----------
# before_job = ["apil_mobile.utils.before_job"]
# after_job = ["apil_mobile.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"apil_mobile.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

