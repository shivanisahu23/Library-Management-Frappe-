import frappe
from frappe.utils import today

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Issue ID",        "fieldname": "name",         "fieldtype": "Link",     "options": "Book Issue", "width": 160},
        {"label": "Member",          "fieldname": "member_name",  "fieldtype": "Data",     "width": 160},
        {"label": "Member Type",     "fieldname": "member_type",  "fieldtype": "Data",     "width": 110},
        {"label": "Book",            "fieldname": "book_title",   "fieldtype": "Data",     "width": 200},
        {"label": "Issue Date",      "fieldname": "issue_date",   "fieldtype": "Date",     "width": 110},
        {"label": "Due Date",        "fieldname": "due_date",     "fieldtype": "Date",     "width": 110},
        {"label": "Days Overdue",    "fieldname": "days_overdue", "fieldtype": "Int",      "width": 110},
        {"label": "Fine Accrued (₹)","fieldname": "fine_accrued", "fieldtype": "Currency", "width": 130},
    ]

def get_data(filters):
    conditions = "bi.status = 'Overdue'"

    if filters and filters.get("member_type"):
        conditions += " AND lm.member_type = %(member_type)s"

    rows = frappe.db.sql("""
        SELECT
            bi.name,
            lm.full_name     AS member_name,
            lm.member_type,
            b.book_title,
            bi.issue_date,
            bi.due_date,
            DATEDIFF(CURDATE(), bi.due_date) AS days_overdue
        FROM `tabBook Issue` bi
        JOIN `tabLibrary Member` lm ON lm.name = bi.library_member
        JOIN `tabBook`           b  ON b.name  = bi.book
        WHERE {conditions}
        ORDER BY days_overdue DESC
    """.format(conditions=conditions), filters or {}, as_dict=True)

    fine_per_day = frappe.db.get_single_value("Library Settings", "fine_per_day") or 5

    for row in rows:
        row["fine_accrued"] = (row["days_overdue"] or 0) * fine_per_day

    return rows
