import frappe

_firebase_app = None


def _get_firebase_app():
	"""Lazily initialise the Firebase Admin SDK from the service-account JSON
	path configured in site_config.json (firebase_service_account_path - not
	committed to the repo). Returns None (and logs once) if it isn't
	configured yet, so push sending is a no-op rather than a hard failure
	until the Firebase project is set up.
	"""
	global _firebase_app
	if _firebase_app is not None:
		return _firebase_app

	cred_path = frappe.conf.get("firebase_service_account_path")
	if not cred_path:
		frappe.logger("apil_mobile.mobile_notifications").warning(
			"firebase_service_account_path not set in site_config.json - push notifications are disabled."
		)
		return None

	import firebase_admin
	from firebase_admin import credentials

	_firebase_app = firebase_admin.initialize_app(credentials.Certificate(cred_path))
	return _firebase_app


def send_push_to_role(role, title, body, data=None):
	"""Send an FCM push to every registered device of every user holding
	`role`. Any send failure is logged, not raised - a push failure must
	never roll back the document submit/insert that triggered it.
	"""
	app = _get_firebase_app()
	if not app:
		return

	users = frappe.get_all("Has Role", filters={"role": role, "parenttype": "User"}, pluck="parent")
	if not users:
		return

	tokens = frappe.get_all(
		"Mobile Device Token", filters={"user": ["in", users]}, pluck="fcm_token"
	)
	if not tokens:
		return

	from firebase_admin import messaging

	messages = [
		messaging.Message(
			notification=messaging.Notification(title=title, body=body),
			data={k: str(v) for k, v in (data or {}).items()},
			token=token,
		)
		for token in tokens
	]

	try:
		messaging.send_each(messages, app=app)
	except Exception:
		frappe.log_error(title="Mobile push notification failed")


def notify_new_weight_priced_document(doc, method=None):
	"""after_insert hook for Sales Order / Sales Invoice. Only notifies when
	the order is actually weight-priced (custom_catalogue_weight set on some
	row) - most draft orders in the system aren't, and shouldn't page
	approvers.
	"""
	if not any(item.get("custom_catalogue_weight") for item in doc.items):
		return

	send_push_to_role(
		"APIL Mobile Approver",
		title=f"{doc.doctype} pending approval",
		body=f"{doc.doctype} {doc.name} for {doc.customer} needs review.",
		data={"doctype": doc.doctype, "name": doc.name},
	)
