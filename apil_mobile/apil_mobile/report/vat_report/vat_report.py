import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Line", "fieldname": "label", "fieldtype": "Data", "width": 220},
		{"label": "Amount", "fieldname": "amount", "fieldtype": "Currency", "width": 150},
	]


def get_data(filters):
	company = filters.get("company")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	output_vat = _sum_vat("Sales Invoice", "Sales Taxes and Charges", company, from_date, to_date)
	input_vat = _sum_vat("Purchase Invoice", "Purchase Taxes and Charges", company, from_date, to_date)

	return [
		{"label": "Output VAT (Sales)", "amount": output_vat},
		{"label": "Input VAT (Purchases)", "amount": input_vat},
		{"label": "Net VAT Payable", "amount": output_vat - input_vat},
	]


def _sum_vat(invoice_doctype, tax_doctype, company, from_date, to_date):
	conditions = ["inv.docstatus = 1", "tax.account_head like %(vat_pattern)s"]
	values = {"vat_pattern": "%VAT%"}

	if company:
		conditions.append("inv.company = %(company)s")
		values["company"] = company

	if from_date:
		conditions.append("inv.posting_date >= %(from_date)s")
		values["from_date"] = from_date

	if to_date:
		conditions.append("inv.posting_date <= %(to_date)s")
		values["to_date"] = to_date

	total = frappe.db.sql(
		"""
		select sum(tax.base_tax_amount)
		from `tab{tax_doctype}` tax
		inner join `tab{invoice_doctype}` inv on inv.name = tax.parent
		where {conditions}
		""".format(
			tax_doctype=tax_doctype,
			invoice_doctype=invoice_doctype,
			conditions=" and ".join(conditions),
		),
		values,
	)
	return total[0][0] or 0
