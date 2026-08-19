import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Production Plan", "fieldname": "name", "fieldtype": "Link", "options": "Production Plan", "width": 150},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 110},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": "Warehouse", "fieldname": "for_warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 150},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("pp.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("status"):
		conditions.append("pp.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("from_date"):
		conditions.append("pp.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("pp.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = ("where " + " and ".join(conditions)) if conditions else ""

	return frappe.db.sql(
		f"""
		select pp.name, pp.posting_date, pp.status, pp.company, pp.for_warehouse
		from `tabProduction Plan` pp
		{where_clause}
		order by pp.posting_date desc, pp.name desc
		""",
		values,
		as_dict=True,
	)
