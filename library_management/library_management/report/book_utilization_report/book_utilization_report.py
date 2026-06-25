import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Book",             "fieldname": "book_title",     "fieldtype": "Link",     "options": "Book", "width": 220},
        {"label": "Category",         "fieldname": "category",       "fieldtype": "Data",     "width": 130},
        {"label": "Publisher",        "fieldname": "publisher",      "fieldtype": "Data",     "width": 150},
        {"label": "Total Copies",     "fieldname": "total_copies",   "fieldtype": "Int",      "width": 110},
        {"label": "Available Copies", "fieldname": "available",      "fieldtype": "Int",      "width": 130},
        {"label": "Times Issued",     "fieldname": "times_issued",   "fieldtype": "Int",      "width": 110},
        {"label": "Currently Issued", "fieldname": "active_issues",  "fieldtype": "Int",      "width": 130},
        {"label": "Times Overdue",    "fieldname": "overdue_count",  "fieldtype": "Int",      "width": 120},
        {"label": "Utilization %",    "fieldname": "utilization_pct","fieldtype": "Percent",  "width": 120},
    ]

def get_data(filters):
    conditions = "1=1"

    if filters and filters.get("category"):
        conditions += " AND b.category = %(category)s"

    rows = frappe.db.sql("""
        SELECT
            b.name                                          AS book_title,
            b.category,
            b.publisher,
            b.total_copies_owned                            AS total_copies,
            b.available_copies                              AS available,
            COUNT(bi.name)                                  AS times_issued,
            SUM(bi.status IN ('Issues', 'Overdue'))         AS active_issues,
            SUM(bi.status = 'Overdue')                      AS overdue_count
        FROM `tabBook` b
        LEFT JOIN `tabBook Issue` bi ON bi.book = b.name
        WHERE {conditions}
        GROUP BY b.name
        ORDER BY times_issued DESC
    """.format(conditions=conditions), filters or {}, as_dict=True)

    for row in rows:
        total = row["total_copies"] or 1
        issued = row["active_issues"] or 0
        row["utilization_pct"] = round((issued / total) * 100, 2)

    return rows
