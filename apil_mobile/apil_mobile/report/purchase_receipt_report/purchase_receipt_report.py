import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Purchase Receipt", "fieldname": "name", "fieldtype": "Link", "options": "Purchase Receipt", "width": 130},
		{"label": "Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": "Supplier Name", "fieldname": "supplier_name", "fieldtype": "Data", "width": 180},
		{"label": "Supplier", "fieldname": "supplier", "fieldtype": "Link", "options": "Supplier", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
		{"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 120},
	]


def get_data(filters):
	conditions = ["pr.docstatus = 1"]
	values = {}

	if filters.get("company"):
		conditions.append("pr.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("supplier"):
		conditions.append("pr.supplier = %(supplier)s")
		values["supplier"] = filters["supplier"]

	if filters.get("from_date"):
		conditions.append("pr.posting_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("pr.posting_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		"""
		select pr.name, pr.posting_date, pr.supplier, pr.supplier_name, pr.company, pr.grand_total
		from `tabPurchase Receipt` pr
		where {conditions}
		order by pr.posting_date desc, pr.name desc
		""".format(conditions=" and ".join(conditions)),
		values,
		as_dict=True,
	)
