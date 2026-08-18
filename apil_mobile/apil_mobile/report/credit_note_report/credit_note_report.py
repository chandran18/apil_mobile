import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Credit Note", "fieldname": "name", "fieldtype": "Link", "options": "Sales Invoice", "width": 130},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": "Against Invoice", "fieldname": "return_against", "fieldtype": "Link", "options": "Sales Invoice", "width": 130},
		{"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	# A Credit Note in ERPNext is a Sales Invoice with is_return = 1, not a
	# separate doctype - grand_total on a return is already negative, so no
	# sign-flipping is needed here.
	conditions = ["si.docstatus = 1", "si.is_return = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("si.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("customer"):
		conditions.append("si.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		"""
		select si.name, si.posting_date, si.customer, si.customer_name, si.company, si.return_against, si.grand_total
		from `tabSales Invoice` si
		where {conditions}
		order by si.posting_date desc, si.name desc
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)
