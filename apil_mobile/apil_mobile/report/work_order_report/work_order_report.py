import frappe


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": "Work Order", "fieldname": "name", "fieldtype": "Link", "options": "Work Order", "width": 150},
		{"label": "Item To Manufacture", "fieldname": "production_item", "fieldtype": "Link", "options": "Item", "width": 150},
		{"label": "Item Name", "fieldname": "item_name", "fieldtype": "Data", "width": 150},
		{"label": "BOM No", "fieldname": "bom_no", "fieldtype": "Link", "options": "BOM", "width": 150},
		{"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": "Sales Order", "fieldname": "sales_order", "fieldtype": "Link", "options": "Sales Order", "width": 150},
		{"label": "Qty To Manufacture", "fieldname": "qty", "fieldtype": "Float", "width": 120},
		{"label": "Manufactured Qty", "fieldname": "produced_qty", "fieldtype": "Float", "width": 120},
		{"label": "Expected Delivery Date", "fieldname": "expected_delivery_date", "fieldtype": "Date", "width": 130},
		{"label": "Company", "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 150},
	]


def get_data(filters):
	conditions = []
	values = {}

	if filters.get("company"):
		conditions.append("wo.company = %(company)s")
		values["company"] = filters["company"]

	if filters.get("status"):
		conditions.append("wo.status = %(status)s")
		values["status"] = filters["status"]

	if filters.get("from_date"):
		conditions.append("wo.planned_start_date >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("wo.planned_start_date <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where_clause = ("where " + " and ".join(conditions)) if conditions else ""

	return frappe.db.sql(
		f"""
		select wo.name, wo.production_item, wo.item_name, wo.bom_no, wo.status,
			wo.sales_order, wo.qty, wo.produced_qty, wo.expected_delivery_date, wo.company
		from `tabWork Order` wo
		{where_clause}
		order by wo.planned_start_date desc, wo.name desc
		""",
		values,
		as_dict=True,
	)
