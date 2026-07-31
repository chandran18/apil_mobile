from datetime import timedelta

import frappe
from frappe.utils import flt, getdate, now_datetime, nowdate

# Doctypes the mobile app is allowed to approve/reject. Kept as an explicit
# allowlist (not "any doctype with a name+docstatus") since approve_document
# calls doc.submit() - we never want an arbitrary doctype name from a client
# request driving a submit.
APPROVABLE_DOCTYPES = {
	"Stock Entry",
	"Sales Order",
	"Sales Invoice",
	"Purchase Order",
	"Purchase Invoice",
	"Payment Entry",
}


def _issue_api_credentials(user_name):
	user = frappe.get_doc("User", user_name)
	api_secret = frappe.generate_hash(length=15)
	if not user.api_key:
		user.api_key = frappe.generate_hash(length=15)
	user.api_secret = api_secret
	user.save(ignore_permissions=True)
	return {"api_key": user.api_key, "api_secret": api_secret}


@frappe.whitelist(allow_guest=True)
def login(usr, pwd):
	"""One-shot email+password -> API key/secret exchange for the mobile
	app's Login screen. Deliberately avoids the normal /api/method/login +
	session-cookie dance: cross-origin cookies on Flutter Web (a different
	port than the backend in dev) are unreliable to get right, and the app
	only ever needs key/secret auth afterwards anyway. Runs the exact same
	authenticate() Frappe itself uses (so login-attempt throttling/lockout
	still applies), just without round-tripping a cookie back to the client.
	"""
	from frappe.auth import LoginManager

	login_manager = LoginManager()
	login_manager.authenticate(user=usr, pwd=pwd)
	login_manager.post_login()
	return _issue_api_credentials(frappe.session.user)


@frappe.whitelist()
def get_my_api_credentials():
	"""Self-service API key/secret re-issuance for an already-authenticated
	session (e.g. a future "regenerate my key" action from within the app).
	Scoped to frappe.session.user only - unlike
	frappe.core.doctype.user.user.generate_keys, this needs no System
	Manager role, since a valid session already proves who's asking.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Not logged in.", frappe.AuthenticationError)
	return _issue_api_credentials(frappe.session.user)


@frappe.whitelist()
def register_device_token(fcm_token, device_type=None, app_version=None):
	"""Upsert the calling user's FCM token. A token can move to a different
	Mobile Device Token record if the device gets a fresh token or is
	re-logged-in as a different user - always keyed by fcm_token, never by a
	client-supplied user.
	"""
	name = frappe.db.get_value("Mobile Device Token", {"fcm_token": fcm_token})
	if name:
		doc = frappe.get_doc("Mobile Device Token", name)
	else:
		doc = frappe.new_doc("Mobile Device Token")
		doc.fcm_token = fcm_token

	doc.user = frappe.session.user
	if device_type:
		doc.device_type = device_type
	if app_version:
		doc.app_version = app_version
	doc.last_seen = now_datetime()
	doc.save(ignore_permissions=True)
	return {"ok": True}


def _pending_stock_entries():
	if not frappe.has_permission("Stock Entry", "submit"):
		return []

	entries = frappe.get_all(
		"Stock Entry",
		filters={"stock_entry_type": "Manufacture", "docstatus": 0},
		fields=["name", "posting_date", "company", "remarks"],
		order_by="creation desc",
	)
	for entry in entries:
		log = frappe.db.get_value(
			"Extrusion Log",
			{"stock_entry": entry.name},
			["name", "date", "shift", "die_no", "sec_no", "ok_pcs", "output"],
			as_dict=True,
		)
		entry["extrusion_log"] = log
	return entries


def _pending_weight_priced(doctype):
	"""doctype is always one of the two hardcoded call sites below, never
	client input - safe to interpolate into the table names.
	"""
	if not frappe.has_permission(doctype, "submit"):
		return []

	date_field = "transaction_date" if doctype == "Sales Order" else "posting_date"
	return frappe.db.sql(
		f"""
		select distinct p.name, p.customer, p.{date_field} as txn_date, p.grand_total
		from `tab{doctype}` p
		inner join `tab{doctype} Item` c on c.parent = p.name
		where p.docstatus = 0 and c.custom_catalogue_weight > 0
		order by p.creation desc
		""",
		as_dict=True,
	)


def _pending_simple(doctype, fields):
	"""Plain "docstatus = 0" draft list for doctypes with no extra business
	filter (unlike Sales Order/Invoice, which only surface weight-priced
	rows). doctype is always one of the hardcoded call sites below.
	"""
	if not frappe.has_permission(doctype, "submit"):
		return []
	return frappe.get_all(
		doctype,
		filters={"docstatus": 0},
		fields=fields,
		order_by="creation desc",
	)


@frappe.whitelist()
def get_pending_approvals():
	"""Everything the calling user can currently act on from the mobile app,
	grouped by document type. Permission-filtered per category so a user only
	ever sees categories they hold submit rights for.
	"""
	return {
		"stock_entries": _pending_stock_entries(),
		"sales_orders": _pending_weight_priced("Sales Order"),
		"sales_invoices": _pending_weight_priced("Sales Invoice"),
		"purchase_orders": _pending_simple(
			"Purchase Order", ["name", "supplier", "transaction_date", "grand_total"]
		),
		"purchase_invoices": _pending_simple(
			"Purchase Invoice", ["name", "supplier", "posting_date", "due_date", "grand_total"]
		),
		"payment_entries": _pending_simple(
			"Payment Entry",
			["name", "party", "posting_date", "payment_type", "paid_amount"],
		),
	}


def _approval_limit_for(doctype):
	"""The most permissive configured limit across the calling user's roles,
	or None if nothing has been configured for any of them - absence of a
	Mobile Approval Limit row means no restriction, not a fabricated policy.
	"""
	# ignore_permissions is safe here: this only ever reads limits for the
	# calling user's own roles (frappe.get_roles(), never a client-supplied
	# role), to compute the limit that already governs them - not arbitrary
	# access to other users' configured limits.
	rows = frappe.get_all(
		"Mobile Approval Limit",
		filters={"role": ["in", frappe.get_roles()], "for_doctype": doctype},
		fields=["unlimited", "max_amount"],
		ignore_permissions=True,
	)
	if not rows:
		return None
	if any(r.unlimited for r in rows):
		return None
	return max(flt(r.max_amount) for r in rows)


@frappe.whitelist()
def get_approval_limits():
	"""Real limits only - a doctype with nothing configured for any of the
	user's roles is reported as unlimited, since that's the actual current
	policy (or lack of one), not a number we're inventing.
	"""
	return {doctype: _approval_limit_for(doctype) for doctype in APPROVABLE_DOCTYPES}


@frappe.whitelist()
def approve_document(doctype, name):
	if doctype not in APPROVABLE_DOCTYPES:
		frappe.throw(f"{doctype} cannot be approved from the mobile app.")

	doc = frappe.get_doc(doctype, name)
	if not frappe.has_permission(doctype, "submit", doc):
		frappe.throw("You are not permitted to approve this document.", frappe.PermissionError)

	limit = _approval_limit_for(doctype)
	if limit is not None:
		amount = flt(doc.get("grand_total") or doc.get("paid_amount") or 0)
		if amount > limit:
			frappe.throw(
				f"This {doctype} ({amount}) exceeds your mobile approval limit of {limit} for {doctype}.",
				frappe.PermissionError,
			)

	doc.submit()
	doc.add_comment("Comment", "Approved via mobile app")
	return {"ok": True, "docstatus": doc.docstatus}


@frappe.whitelist()
def get_audit_log():
	"""Real actions taken through this app - not a fabricated activity feed.
	Reads the comments approve_document/reject_document actually leave on
	documents, so this only ever shows what genuinely happened. Raw SQL
	against Comment doesn't check per-document permission the way
	frappe.get_all would, so scope to only doctypes the calling user can
	currently read - never blindly the full APPROVABLE_DOCTYPES allowlist.
	"""
	readable = [d for d in APPROVABLE_DOCTYPES if frappe.has_permission(d, "read")]
	if not readable:
		return []

	placeholders = ", ".join(["%s"] * len(readable))
	rows = frappe.db.sql(
		f"""
		select reference_doctype, reference_name, content, owner, creation
		from `tabComment`
		where comment_type = 'Comment'
		and reference_doctype in ({placeholders})
		and (content like '%%via mobile app%%')
		order by creation desc
		limit 20
		""",
		tuple(readable),
		as_dict=True,
	)
	for r in rows:
		r["action"] = "Approved" if "Approved" in r.content else ("Rejected" if "Rejected" in r.content else "Actioned")
	return rows


def _month_start():
	return getdate(nowdate()).replace(day=1)


@frappe.whitelist()
def get_dashboard_summary():
	"""Executive Dashboard numbers. Each section is gated on report/read
	permission for its underlying doctype so a user without Accounts access,
	say, just doesn't get that section rather than seeing a zero that looks
	like a real balance.
	"""
	summary = {}
	month_start = _month_start()
	today = nowdate()

	if frappe.has_permission("Purchase Invoice", "report"):
		summary["outstanding_payables"] = flt(
			frappe.db.sql(
				"select sum(outstanding_amount) from `tabPurchase Invoice` where docstatus = 1"
			)[0][0]
		)
		summary["monthly_purchase_spend"] = flt(
			frappe.db.sql(
				"""select sum(base_grand_total) from `tabPurchase Invoice`
				where docstatus = 1 and posting_date between %s and %s""",
				(month_start, today),
			)[0][0]
		)
		summary["top_suppliers"] = frappe.db.sql(
			"""select supplier, sum(base_grand_total) as spend
			from `tabPurchase Invoice`
			where docstatus = 1 and posting_date between %s and %s
			group by supplier order by spend desc limit 5""",
			(month_start, today),
			as_dict=True,
		)

	if frappe.has_permission("Sales Invoice", "report"):
		summary["outstanding_receivables"] = flt(
			frappe.db.sql(
				"select sum(outstanding_amount) from `tabSales Invoice` where docstatus = 1"
			)[0][0]
		)

	if frappe.has_permission("GL Entry", "report"):
		summary["cash_position"] = flt(
			frappe.db.sql(
				"""select sum(debit - credit) from `tabGL Entry` gl
				inner join `tabAccount` acc on acc.name = gl.account
				where gl.is_cancelled = 0 and acc.account_type in ('Cash', 'Bank')"""
			)[0][0]
		)

	if frappe.has_permission("Extrusion Log", "report"):
		summary["extrusion_output_this_month"] = flt(
			frappe.db.sql(
				"""select sum(output) from `tabExtrusion Log`
				where docstatus = 1 and date between %s and %s""",
				(month_start, today),
			)[0][0]
		)

	approvals = get_pending_approvals()
	summary["pending_approvals_count"] = sum(len(v) for v in approvals.values())

	# "Needs your decision" preview on the dashboard - up to 3 items across
	# every approvable category, newest first, so it's not always just the
	# same doctype's queue.
	party_fields = {
		"stock_entries": "company",
		"sales_orders": "customer",
		"sales_invoices": "customer",
		"purchase_orders": "supplier",
		"purchase_invoices": "supplier",
		"payment_entries": "party",
	}
	doctype_labels = {
		"stock_entries": "Stock Entry",
		"sales_orders": "Sales Order",
		"sales_invoices": "Sales Invoice",
		"purchase_orders": "Purchase Order",
		"purchase_invoices": "Purchase Invoice",
		"payment_entries": "Payment Entry",
	}
	preview = []
	for key, rows in approvals.items():
		for row in rows:
			preview.append({
				"doctype": doctype_labels[key],
				"name": row.get("name"),
				"party": row.get(party_fields[key]),
				"amount": row.get("grand_total") or row.get("paid_amount"),
			})
	summary["needs_your_decision"] = preview[:3]

	return summary


@frappe.whitelist()
def get_alerts():
	"""Read-only, computed each call - no stored/dismissable state in this
	round (see plan notes). Grouped the same way the app's Alert Centre
	displays them: critical / financial / operational.
	"""
	alerts = {"critical": [], "financial": [], "operational": []}

	approvals = get_pending_approvals()
	pending_count = sum(len(v) for v in approvals.values())
	if pending_count:
		alerts["critical"].append({
			"title": "Unapproved transactions",
			"detail": f"{pending_count} document(s) awaiting your approval.",
		})

	if frappe.has_permission("Purchase Invoice", "report"):
		overdue = frappe.db.sql(
			"""select name, supplier, outstanding_amount, due_date
			from `tabPurchase Invoice`
			where docstatus = 1 and outstanding_amount > 0 and due_date < %s
			order by due_date asc limit 20""",
			(nowdate(),),
			as_dict=True,
		)
		for row in overdue:
			alerts["financial"].append({
				"title": f"Overdue: {row.supplier}",
				"detail": f"{row.name} - {row.outstanding_amount} overdue since {row.due_date}",
				"doctype": "Purchase Invoice",
				"name": row.name,
			})

	if frappe.has_permission("Stock Ledger Entry", "report"):
		for row in _out_of_stock_rows(limit=20):
			alerts["operational"].append({
				"title": f"Out of stock: {row.item_code}",
				"detail": f"{row.warehouse} - {row.actual_qty} on hand",
			})

	return alerts


def _period_range(period):
	today = getdate(nowdate())
	if period == "7D":
		return today - timedelta(days=6), today, "day", "%Y-%m-%d"
	if period == "MTD":
		return today.replace(day=1), today, "day", "%Y-%m-%d"
	if period == "QTD":
		quarter_start_month = ((today.month - 1) // 3) * 3 + 1
		return today.replace(month=quarter_start_month, day=1), today, "month", "%Y-%m"
	# YTD
	return today.replace(month=1, day=1), today, "month", "%Y-%m"


@frappe.whitelist()
def get_spend_trend(period="YTD"):
	"""Purchase spend over time - the honest equivalent of a "revenue trend"
	for this business: Sales Invoice activity is close to zero on f.com, but
	Purchase Invoice activity is real and continuous. Buckets by day (7D/MTD)
	or by month (QTD/YTD) since that's the granularity the real data
	actually supports - see the mobile_api plan notes on thin-data handling.
	"""
	if not frappe.has_permission("Purchase Invoice", "report"):
		return {"points": [], "labels": [], "total": 0, "is_thin": True}

	start, end, bucket, fmt = _period_range(period)
	# %% escapes the literal % for pymysql's own %-style param substitution -
	# without it, DATE_FORMAT's %Y/%m get mistaken for query parameters.
	date_expr = "posting_date" if bucket == "day" else "DATE_FORMAT(posting_date, '%%Y-%%m-01')"

	rows = frappe.db.sql(
		f"""
		select {date_expr} as bucket, sum(base_grand_total) as total
		from `tabPurchase Invoice`
		where docstatus = 1 and posting_date between %s and %s
		group by bucket
		order by bucket asc
		""",
		(start, end),
		as_dict=True,
	)
	by_bucket = {getdate(r.bucket).strftime(fmt): flt(r.total) for r in rows}

	# Fill every day/month in the range with its real total (0 where nothing
	# was posted) rather than only the buckets with rows - a quiet month is
	# a real data point, not a gap to skip; skipping it would silently
	# collapse the calendar axis (e.g. May appearing to connect to July).
	labels = []
	cursor = start.replace(day=1) if bucket == "month" else start
	while cursor <= end:
		labels.append(cursor.strftime(fmt))
		if bucket == "day":
			cursor = cursor + timedelta(days=1)
		else:
			next_month = 1 if cursor.month == 12 else cursor.month + 1
			next_year = cursor.year + 1 if cursor.month == 12 else cursor.year
			cursor = cursor.replace(year=next_year, month=next_month, day=1)
	points = [by_bucket.get(label, 0.0) for label in labels]
	total = sum(points)

	return {
		"points": points,
		"labels": labels,
		"total": total,
		"period": period,
		# Fewer than 5 buckets isn't enough to read as a trend - the client
		# falls back to a thin-data card instead of drawing a misleading line.
		"is_thin": len(points) < 5,
	}


@frappe.whitelist()
def get_expense_breakdown():
	"""Real expense mix by GL account (root_type Expense), not the demo
	spec's fictional Materials/Payroll/Logistics categories - whatever
	accounts this company actually posts expenses against.
	"""
	if not frappe.has_permission("GL Entry", "report"):
		return {"slices": []}

	rows = frappe.db.sql(
		"""
		select acc.account_name as label, sum(gl.debit - gl.credit) as amount
		from `tabGL Entry` gl
		inner join `tabAccount` acc on acc.name = gl.account
		where gl.is_cancelled = 0 and acc.root_type = 'Expense'
		group by acc.account_name
		having amount > 0
		order by amount desc
		""",
		as_dict=True,
	)

	total = sum(flt(r.amount) for r in rows)
	if not total:
		return {"slices": []}

	top = rows[:5]
	other_amount = total - sum(flt(r.amount) for r in top)
	slices = [{"label": r.label, "amount": flt(r.amount), "share": flt(r.amount) / total * 100} for r in top]
	if other_amount > 0:
		slices.append({"label": "Other", "amount": other_amount, "share": other_amount / total * 100})

	return {"slices": slices, "total": total}


@frappe.whitelist()
def get_my_context():
	"""Real identity/roles for the More screen's Account section - not a
	fabricated persona like the reference app's "CEO, Meridian Industrial
	Group". Excludes All/Guest/Desk User: every desk-enabled user holds these,
	so they say nothing about what this particular person can actually do.
	"""
	user = frappe.session.user
	roles = [r for r in frappe.get_roles(user) if r not in ("All", "Guest", "Desk User")]
	return {
		"user": user,
		"full_name": frappe.db.get_value("User", user, "full_name") or user,
		"roles": roles,
	}


def _out_of_stock_rows(limit=None):
	"""Bins currently at or below zero - the one real, always-meaningful stock
	signal on this site (Item Reorder has zero configured rows, so "below
	reorder level" isn't a real metric here - see get_inventory_summary).
	"""
	query = """
		select item_code, warehouse, actual_qty from `tabBin`
		where actual_qty <= 0 order by modified desc
	"""
	if limit:
		query += f" limit {int(limit)}"
	return frappe.db.sql(query, as_dict=True)


@frappe.whitelist()
def get_module_summary():
	"""Real counts for the More screen's module tiles. Each key only appears
	if the calling user actually holds read access to its underlying
	doctype(s) - same permission-gated pattern as get_dashboard_summary, so a
	restricted user never sees a tile backed by data they can't act on.
	"""
	summary = {}

	if frappe.has_permission("Sales Order", "read"):
		summary["sales"] = {
			"open_orders": frappe.db.count("Sales Order", {"docstatus": 0}),
		}

	if frappe.has_permission("Purchase Order", "read") or frappe.has_permission("Purchase Invoice", "read"):
		approvals = get_pending_approvals()
		summary["procurement"] = {
			"requests_open": len(approvals["purchase_orders"]) + len(approvals["purchase_invoices"]),
		}

	if frappe.has_permission("Stock Ledger Entry", "report"):
		summary["inventory"] = {"out_of_stock": len(_out_of_stock_rows())}

	return summary


@frappe.whitelist()
def get_sales_summary():
	"""Real Sales module numbers. f.com currently has zero Sales Orders and
	zero Sales Invoices in the database (checked directly) - not a bug in
	this endpoint, just the actual current state. The screen is expected to
	show that honestly rather than a chart with nothing behind it.
	"""
	if not frappe.has_permission("Sales Order", "read"):
		return {}

	summary = {
		"open_orders": frappe.db.count("Sales Order", {"docstatus": 0}),
		"submitted_orders": frappe.db.count("Sales Order", {"docstatus": 1}),
	}
	if frappe.has_permission("Customer", "read"):
		summary["customers"] = frappe.db.count("Customer")
	if frappe.has_permission("Sales Invoice", "report"):
		summary["invoiced_total"] = flt(
			frappe.db.sql("select sum(base_grand_total) from `tabSales Invoice` where docstatus = 1")[0][0]
		)
		summary["outstanding_receivables"] = flt(
			frappe.db.sql("select sum(outstanding_amount) from `tabSales Invoice` where docstatus = 1")[0][0]
		)
	return summary


@frappe.whitelist()
def get_inventory_summary():
	"""Real stock-value and out-of-stock picture. Deliberately doesn't
	include "below reorder level" or "expiring soon" cards like the reference
	design: Item Reorder has zero configured rows and Batch has zero rows
	with an expiry date on this site (checked directly), so those numbers
	would always read 0 - not a real signal, just an unconfigured feature.
	"""
	if not frappe.has_permission("Stock Ledger Entry", "report"):
		return {}

	by_warehouse = frappe.db.sql(
		"""
		select warehouse, sum(actual_qty * valuation_rate) as value
		from `tabBin` where actual_qty != 0
		group by warehouse having value > 0
		order by value desc
		""",
		as_dict=True,
	)
	total_value = sum(flt(r.value) for r in by_warehouse)
	out_of_stock = _out_of_stock_rows(limit=20)

	return {
		"total_stock_value": total_value,
		"by_warehouse": [{"warehouse": r.warehouse, "value": flt(r.value)} for r in by_warehouse],
		"out_of_stock_count": len(_out_of_stock_rows()),
		"out_of_stock": out_of_stock,
	}


@frappe.whitelist()
def get_procurement_summary():
	"""Real procurement numbers - open PO commitment, on-time delivery and
	top supplier spend. No "pending requests" beyond what's already in the
	approval queue: this site doesn't use Material Request. No price
	comparison across suppliers either - checked directly, and every
	multi-supplier "item" in this data is a generic expense bucket
	(Maintainance, Office Running Expenses, Fuel...) rather than a real SKU,
	so a same-item price comparison would just be noise dressed up as insight.
	"""
	if not (frappe.has_permission("Purchase Order", "report") or frappe.has_permission("Purchase Invoice", "report")):
		return {}

	summary = {}

	open_po = frappe.db.sql(
		"""
		select count(*) as cnt, sum(grand_total) as val
		from `tabPurchase Order`
		where docstatus = 1 and (per_received < 100 or per_billed < 100)
		""",
		as_dict=True,
	)[0]
	summary["open_pos"] = {"count": open_po.cnt or 0, "committed_value": flt(open_po.val)}

	approvals = get_pending_approvals()
	summary["pending_requests"] = len(approvals["purchase_orders"]) + len(approvals["purchase_invoices"])

	on_time = frappe.db.sql(
		"""
		select
			sum(case when pr.posting_date <= poi.schedule_date then 1 else 0 end) as on_time,
			count(*) as total
		from `tabPurchase Receipt Item` pri
		inner join `tabPurchase Receipt` pr on pr.name = pri.parent and pr.docstatus = 1
		inner join `tabPurchase Order Item` poi on poi.name = pri.purchase_order_item
		""",
		as_dict=True,
	)[0]
	summary["on_time_supply_pct"] = round(on_time.on_time / on_time.total * 100, 1) if on_time.total else None

	supplier_performance = frappe.db.sql(
		"""
		select supplier, sum(base_grand_total) as spend, count(*) as invoice_count
		from `tabPurchase Invoice`
		where docstatus = 1
		group by supplier order by spend desc limit 5
		""",
		as_dict=True,
	)
	supplier_on_time = {
		r.supplier: r
		for r in frappe.db.sql(
			"""
			select po.supplier,
				sum(case when pr.posting_date <= poi.schedule_date then 1 else 0 end) as on_time,
				count(*) as total
			from `tabPurchase Receipt Item` pri
			inner join `tabPurchase Receipt` pr on pr.name = pri.parent and pr.docstatus = 1
			inner join `tabPurchase Order Item` poi on poi.name = pri.purchase_order_item
			inner join `tabPurchase Order` po on po.name = poi.parent
			group by po.supplier
			""",
			as_dict=True,
		)
	}
	for row in supplier_performance:
		s = supplier_on_time.get(row["supplier"])
		row["on_time_pct"] = round(s.on_time / s.total * 100, 1) if s and s.total else None
	summary["supplier_performance"] = supplier_performance

	return summary


@frappe.whitelist()
def reject_document(doctype, name, reason=None):
	if doctype not in APPROVABLE_DOCTYPES:
		frappe.throw(f"{doctype} cannot be rejected from the mobile app.")

	doc = frappe.get_doc(doctype, name)
	if not frappe.has_permission(doctype, "write", doc):
		frappe.throw("You are not permitted to act on this document.", frappe.PermissionError)

	# Left in Draft intentionally - the desk user who created it fixes it and
	# resubmits for approval; the mobile app never deletes or cancels.
	doc.add_comment("Comment", f"Rejected via mobile app: {reason or 'no reason given'}")
	return {"ok": True}
