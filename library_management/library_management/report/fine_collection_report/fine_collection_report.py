import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Fine ID",          "fieldname": "name",          "fieldtype": "Link",     "options": "Library Fine", "width": 160},
        {"label": "Member",           "fieldname": "member_name",   "fieldtype": "Data",     "width": 160},
        {"label": "Member Type",      "fieldname": "member_type",   "fieldtype": "Data",     "width": 110},
        {"label": "Book",             "fieldname": "book_title",    "fieldtype": "Data",     "width": 200},
        {"label": "Fine Date",        "fieldname": "fine_raised_on","fieldtype": "Date",     "width": 110},
        {"label": "Days Overdue",     "fieldname": "days_overdue",  "fieldtype": "Int",      "width": 110},
        {"label": "Fine Amount (₹)",  "fieldname": "fine_amount",   "fieldtype": "Currency", "width": 130},
        {"label": "Amount Paid (₹)",  "fieldname": "amount_paid",   "fieldtype": "Currency", "width": 130},
        {"label": "Outstanding (₹)",  "fieldname": "outstanding",   "fieldtype": "Currency", "width": 130},
        {"label": "Status",           "fieldname": "status",        "fieldtype": "Data",     "width": 120},
    ]

def get_data(filters):
    conditions = "1=1"

    if filters and filters.get("from_date"):
        conditions += " AND lf.fine_raised_on >= %(from_date)s"
    if filters and filters.get("to_date"):
        conditions += " AND lf.fine_raised_on <= %(to_date)s"
    if filters and filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"
    if filters and filters.get("status"):
        conditions += " AND lf.status = %(status)s"

    rows = frappe.db.sql("""
        SELECT
            lf.name,
            lm.full_name      AS member_name,
            lm.member_type,
            b.book_title,
            lf.fine_raised_on,
            lf.days_overdue,
            lf.fine_amount,
            lf.amount_paid,
            lf.outstanding,
            lf.status
        FROM `tabLibrary Fine` lf
        JOIN `tabLibrary Member` lm ON lm.name = lf.library_member
        JOIN `tabBook`           b  ON b.name  = lf.book
        WHERE {conditions}
        ORDER BY lf.fine_raised_on DESC
    """.format(conditions=conditions), filters or {}, as_dict=True)

    return rows
