# Copyright (c) 2026, Shivani Sahu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, today, date_diff


class BookReturn(Document):

    def validate(self):
        self.validate_issue()
        self.set_return_date()
        self.calculate_overdue()

    def on_submit(self):
        self.update_book_issue()
        self.increment_book_copies()
        self.create_fine_if_overdue()
        self.update_member_summary()

    def on_cancel(self):
        self.reverse_book_issue()
        self.decrement_book_copies()
        self.cancel_fine()
        self.update_member_summary()


    def validate_issue(self):
        if not self.book_issue_refrence:
            frappe.throw(_("Please select a Book Issue reference."))

        issue = frappe.get_doc("Book Issue", self.book_issue_refrence)

        if issue.status == "Returned":
            frappe.throw(_("This book has already been returned."))

        self.library_member = issue.library_member
        self.book = issue.book
        self.due_date = issue.due_date

    def set_return_date(self):
        if not self.return_date:
            self.return_date = today()

    def calculate_overdue(self):
        if not self.due_date or not self.return_date:
            return
        days = date_diff(self.return_date, self.due_date)
        self.days_overdue = max(0, days)

        fine_per_day = frappe.db.get_single_value("Library Settings", "fine_per_day") or 5
        self.fine_applicable = self.days_overdue * fine_per_day


    def update_book_issue(self):
        frappe.db.set_value("Book Issue", self.book_issue_refrence, {
            "status": "Returned",
            "actual_return_date": self.return_date,
        })

    def increment_book_copies(self):
        book = frappe.get_doc("Book", self.book)
        book.return_copy()

    def create_fine_if_overdue(self):
        if self.days_overdue <= 0:
            return

        if frappe.db.exists("Library Fine", {"book_issue_reference": self.book_issue_refrence}):
            return

        customer = frappe.db.get_value("Library Member", self.library_member, "customer")
        fine_per_day = frappe.db.get_single_value("Library Settings", "fine_per_day") or 5

        fine = frappe.get_doc({
            "doctype": "Library Fine",
            "naming_series": "LIB-FIN-",
            "library_member": self.library_member,
            "customer": customer,
            "book_issue_reference": self.book_issue_refrence,
            "book": self.book,
            "fine_raised_on": today(),
            "days_overdue": self.days_overdue,
            "fine_per_day": fine_per_day,
            "fine_amount": self.fine_applicable,
            "amount_paid": 0,
            "outstanding": self.fine_applicable,
            "status": "Unpaid",
        })
        fine.insert(ignore_permissions=True)
        frappe.msgprint(
            _("Fine of ₹{0} raised for {1} overdue day(s).").format(
                self.fine_applicable, self.days_overdue
            ),
            alert=True
        )


    def reverse_book_issue(self):
        frappe.db.set_value("Book Issue", self.book_issue_refrence, {
            "status": "Issues",
            "actual_return_date": None,
        })

    def decrement_book_copies(self):
        book = frappe.get_doc("Book", self.book)
        book.issue_copy()

    def cancel_fine(self):
        fine = frappe.db.get_value(
            "Library Fine",
            {"book_issue_reference": self.book_issue_refrence},
            "name"
        )
        if fine:
            fine_doc = frappe.get_doc("Library Fine", fine)
            if fine_doc.docstatus == 1:
                fine_doc.cancel()
            elif fine_doc.docstatus == 0:
                frappe.delete_doc("Library Fine", fine, ignore_permissions=True)


    def update_member_summary(self):
        member = frappe.get_doc("Library Member", self.library_member)
        member.update_summary()
