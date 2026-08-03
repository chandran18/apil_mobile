import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Shift Production Log", "fieldname": "name", "fieldtype": "Link", "options": "Shift Production Log", "width": 150},
		{"label": "Date", "fieldname": "date", "fieldtype": "Date", "width": 95},
		{"label": "Shift", "fieldname": "shift", "fieldtype": "Data", "width": 60},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": "Total Input (Kg)", "fieldname": "total_input", "fieldtype": "Float", "width": 110},
		{"label": "Total Output (Kg)", "fieldname": "total_output", "fieldtype": "Float", "width": 110},
		{"label": "OK Pcs", "fieldname": "total_ok_pcs", "fieldtype": "Int", "width": 80},
		{"label": "Rec %", "fieldname": "overall_rec_percent", "fieldtype": "Percent", "width": 80},
	]


def get_data(filters):
	conditions = ["spl.docstatus = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("spl.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("shift"):
		conditions.append("spl.shift = %(shift)s")
		values["shift"] = filters["shift"]

	if filters.get("from_date"):
		conditions.append("spl.date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("spl.date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		"""
		select spl.name, spl.date, spl.shift, spl.company,
			spl.total_input, spl.total_output, spl.total_ok_pcs, spl.overall_rec_percent
		from `tabShift Production Log` spl
		where {conditions}
		order by spl.date desc, spl.name desc
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)
