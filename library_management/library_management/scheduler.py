import frappe
from frappe.utils import today, getdate


def mark_overdue_issues():
    overdue = frappe.get_all("Book Issue",
        filters={
            "status": "Issues",
            "due_date": ("<", today())
        },
        fields=["name", "library_member", "book", "due_date"]
    )

    count = 0
    for issue in overdue:
        frappe.db.set_value("Book Issue", issue.name, "status", "Overdue")
        count += 1

    if count:
        frappe.db.commit()
        frappe.logger().info(f"Library Scheduler: {count} issues marked Overdue")

    return f"{count} issues marked as Overdue"


def send_overdue_emails():
    settings = frappe.get_single("Library Settings")
    if not settings.enable_email_notifications:
        return
    if not settings.overdue_email_template:
        return

    overdue = frappe.get_all("Book Issue",
        filters={"status": "Overdue"},
        fields=["name", "library_member", "book", "due_date"]
    )

    sent = 0
    for issue in overdue:
        try:
            member = frappe.get_doc("Library Member", issue.library_member)
            if not member.email:
                continue

            book_title = frappe.db.get_value("Book", issue.book, "book_title")
            fine_per_day = settings.fine_per_day or 5
            from frappe.utils import date_diff
            days_overdue = date_diff(today(), str(issue.due_date).split(" ")[0])
            fine_accrued = days_overdue * fine_per_day

            frappe.sendmail(
                recipients=[member.email],
                template=settings.overdue_email_template,
                args={
                    "member_name": member.full_name,
                    "book_title": book_title,
                    "due_date": issue.due_date,
                    "days_overdue": days_overdue,
                    "fine_accrued": fine_accrued,
                    "issue_id": issue.name,
                },
                subject=f"Overdue Book Reminder — {book_title}",
            )
            sent += 1
        except Exception as e:
            frappe.log_error(str(e), "Library Scheduler - Email Failed")

    frappe.logger().info(f"Library Scheduler: {sent} overdue emails sent")
    return f"{sent} emails sent"


def expire_memberships():
    expired = frappe.get_all("Library Member",
        filters={
            "membership_status": "Active",
            "membership_expire_date": ("<", today())
        },
        fields=["name", "full_name"]
    )

    count = 0
    for m in expired:
        frappe.db.set_value("Library Member", m.name, "membership_status", "Expired")
        count += 1

    if count:
        frappe.db.commit()
        frappe.logger().info(f"Library Scheduler: {count} memberships expired")

    return f"{count} memberships expired" 