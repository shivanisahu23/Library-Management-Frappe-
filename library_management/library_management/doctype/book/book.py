# Copyright (c) 2026, Klaimify Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class Book(Document):

    def before_insert(self):
        if self.total_copies and not self.available_copies:
            self.available_copies = self.total_copies

    def validate(self):
        self.validate_copies()
        self.set_status()

    def validate_copies(self):
        if self.total_copies < 0:
            frappe.throw(_("Total copies cannot be negative."))

        if self.available_copies is None:
            self.available_copies = self.total_copies

        if self.available_copies < 0:
            frappe.throw(_("Available copies cannot be negative."))

        if self.available_copies > self.total_copies:
            frappe.throw(
                _("Available copies ({0}) cannot exceed total copies ({1}).").format(
                    self.available_copies, self.total_copies
                )
            )

    def set_status(self):
        if self.is_new():
            if not self.status:
                self.status = "Available"
            return

        if self.available_copies == 0:
            self.status = "Fully Issued"
        elif self.available_copies > 0:
            self.status = "Available"


    def issue_copy(self):
        self.reload()  
        if self.available_copies <= 0:
            frappe.throw(
                _("No copies of '{0}' are available for issue.").format(self.book_title)
            )
        self.available_copies -= 1
        self.set_status()
        self.save(ignore_permissions=True)

    def return_copy(self):
        self.reload()
        if self.available_copies >= self.total_copies:
            frappe.throw(
                _("All copies of '{0}' are already marked available. "
                  "Check for duplicate returns.").format(self.book_title)
            )
        self.available_copies += 1
        self.set_status()
        self.save(ignore_permissions=True)