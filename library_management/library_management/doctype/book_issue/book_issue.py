# Copyright (c) 2026, Shivani Sahu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, today, date_diff


class BookIssue(Document):

    def validate(self):
        self.validate_member()
        self.validate_book_availability()
        self.validate_member_book_limit()
        self.set_due_date()
        self.set_issued_by()

    def on_submit(self):
        self.decrement_book_copies()
        self.update_member_summary()

    def on_cancel(self):
        self.increment_book_copies()
        self.update_member_summary()


    def validate_member(self):
        member = frappe.get_doc("Library Member", self.library_member)

        if member.membership_status == "Expired":
            frappe.throw(_("Member {0}'s membership has expired on {1}. Please renew before issuing books.").format(
                member.full_name, member.membership_expire_date
            ))

        if member.membership_status == "Suspended":
            frappe.throw(_("Member {0}'s membership is suspended.").format(member.full_name))

    def validate_book_availability(self):
        if self.status in ("Returned",):
            return
        available = frappe.db.get_value("Book", self.book, "available_copies")
        if available is None:
            frappe.throw(_("Book not found."))
        if int(available) <= 0:
            frappe.throw(_("No copies of this book are currently available for issue."))

    def validate_member_book_limit(self):
        member = frappe.get_doc("Library Member", self.library_member)
        member_type = frappe.get_doc("Member Type", member.member_type)
        max_allowed = member_type.max_books_allowed or 3

        current_issued = frappe.db.count("Book Issue", {
            "library_member": self.library_member,
            "status": ["in", ["Issues", "Overdue"]],
            "name": ("!=", self.name)
        })

        if current_issued >= max_allowed:
            frappe.throw(_("Member {0} already has {1} book(s) issued. Maximum allowed is {2}.").format(
                member.full_name, current_issued, max_allowed
            ))

    def set_due_date(self):
        if self.due_date:
            return
        if not self.issue_date:
            self.issue_date = today()

        member = frappe.get_doc("Library Member", self.library_member)
        member_type = frappe.get_doc("Member Type", member.member_type)

        loan_days = member_type.loan_period_days
        if not loan_days:
            loan_days = frappe.db.get_single_value("Library Settings", "default_loan_period") or 14

        from frappe.utils import add_days
        self.due_date = add_days(self.issue_date, int(loan_days))

    def set_issued_by(self):
        if not self.issued_by:
            self.issued_by = frappe.session.user


    def decrement_book_copies(self):
        book = frappe.get_doc("Book", self.book)
        book.issue_copy()

    def increment_book_copies(self):
        book = frappe.get_doc("Book", self.book)
        book.return_copy()


    def update_member_summary(self):
        member = frappe.get_doc("Library Member", self.library_member)
        member.update_summary()



@frappe.whitelist()
def mark_overdue():
    overdue_issues = frappe.get_all("Book Issue",
        filters={
            "status": "Issues",
            "due_date": ("<", today())
        },
        fields=["name", "library_member", "book", "due_date"]
    )

    count = 0
    for issue in overdue_issues:
        frappe.db.set_value("Book Issue", issue.name, "status", "Overdue")
        count += 1

    frappe.db.commit()
    return f"{count} issues marked as Overdue"