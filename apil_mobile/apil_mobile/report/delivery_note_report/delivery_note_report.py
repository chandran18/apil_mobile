import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Delivery Note", "fieldname": "name", "fieldtype": "Link", "options": "Delivery Note", "width": 130},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	conditions = ["dn.docstatus = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("dn.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("customer"):
		conditions.append("dn.customer = %(customer)s")
		values["customer"] = filters["customer"]

	if filters.get("from_date"):
		conditions.append("dn.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("dn.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		"""
		select dn.name, dn.posting_date, dn.customer, dn.customer_name, dn.company, dn.status, dn.grand_total
		from `tabDelivery Note` dn
		where {conditions}
		order by dn.posting_date desc, dn.name desc
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)
