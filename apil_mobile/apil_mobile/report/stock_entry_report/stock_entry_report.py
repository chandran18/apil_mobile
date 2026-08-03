import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Stock Entry", "fieldname": "name", "fieldtype": "Link", "options": "Stock Entry", "width": 130},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": "Type", "fieldname": "stock_entry_type", "fieldtype": "Data", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": "Outgoing Value", "fieldname": "total_outgoing_value", "fieldtype": "Currency", "width": 120},
		{"label": "Incoming Value", "fieldname": "total_incoming_value", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	conditions = ["se.docstatus = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("se.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("stock_entry_type"):
		conditions.append("se.stock_entry_type = %(stock_entry_type)s")
		values["stock_entry_type"] = filters["stock_entry_type"]

	if filters.get("from_date"):
		conditions.append("se.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("se.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		"""
		select se.name, se.posting_date, se.stock_entry_type, se.company,
			se.total_outgoing_value, se.total_incoming_value
		from `tabStock Entry` se
		where {conditions}
		order by se.posting_date desc, se.name desc
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)
