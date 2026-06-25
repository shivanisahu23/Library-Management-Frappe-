import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Member",          "fieldname": "member_name",   "fieldtype": "Data",     "width": 160},
        {"label": "Member Type",     "fieldname": "member_type",   "fieldtype": "Data",     "width": 110},
        {"label": "Total Issued",    "fieldname": "total_issued",  "fieldtype": "Int",      "width": 110},
        {"label": "Returned",        "fieldname": "total_returned","fieldtype": "Int",      "width": 100},
        {"label": "Currently Issued","fieldname": "active_issues", "fieldtype": "Int",      "width": 130},
        {"label": "Overdue",         "fieldname": "overdue_count", "fieldtype": "Int",      "width": 90},
        {"label": "Total Fines (₹)", "fieldname": "total_fines",   "fieldtype": "Currency", "width": 130},
        {"label": "Amount Paid (₹)", "fieldname": "amount_paid",   "fieldtype": "Currency", "width": 130},
        {"label": "Outstanding (₹)", "fieldname": "outstanding",   "fieldtype": "Currency", "width": 130},
    ]

def get_data(filters):
    conditions = "1=1"

    if filters and filters.get("from_date"):
        conditions += " AND bi.issue_date >= %(from_date)s"
    if filters and filters.get("to_date"):
        conditions += " AND bi.issue_date <= %(to_date)s"
    if filters and filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"

    rows = frappe.db.sql("""
        SELECT
            lm.full_name                                        AS member_name,
            lm.member_type,
            COUNT(bi.name)                                      AS total_issued,
            SUM(bi.status = 'Returned')                         AS total_returned,
            SUM(bi.status = 'Issues')                           AS active_issues,
            SUM(bi.status = 'Overdue')                          AS overdue_count,
            IFNULL(SUM(lf.fine_amount), 0)                      AS total_fines,
            IFNULL(SUM(lf.amount_paid), 0)                      AS amount_paid,
            IFNULL(SUM(lf.outstanding), 0)                      AS outstanding
        FROM `tabLibrary Member` lm
        LEFT JOIN `tabBook Issue`   bi ON bi.library_member = lm.name AND {conditions}
        LEFT JOIN `tabLibrary Fine` lf ON lf.library_member = lm.name
        GROUP BY lm.name
        ORDER BY total_issued DESC
    """.format(conditions=conditions), filters or {}, as_dict=True)

    return rows
