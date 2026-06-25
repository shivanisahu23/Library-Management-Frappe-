# Copyright (c) 2026, Shivani Sahu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today


class LibraryFine(Document):

    def validate(self):
        self.validate_amount()
        self.set_customer()
        self.calculate_outstanding()

    def on_submit(self):
        self.create_sales_invoice()
        self.update_member_summary()

    def on_cancel(self):
        self.cancel_sales_invoice()
        self.update_member_summary()


    def validate_amount(self):
        if self.fine_amount <= 0:
            frappe.throw(_("Fine amount must be greater than zero."))

        if self.amount_paid > self.fine_amount:
            frappe.throw(_("Amount paid cannot exceed fine amount of ₹{0}.").format(
                self.fine_amount
            ))

    def set_customer(self):
        if not self.customer and self.library_member:
            self.customer = frappe.db.get_value(
                "Library Member", self.library_member, "customer"
            )

    def calculate_outstanding(self):
        self.outstanding = self.fine_amount - (self.amount_paid or 0)

        if self.outstanding <= 0:
            self.status = "Paid"
        elif self.amount_paid > 0:
            self.status = "Partially Paid"
        else:
            self.status = "Unpaid"


    @frappe.whitelist()
    def waive_fine(self, reason=None):
        if not frappe.has_permission("Library Fine", "write"):
            frappe.throw(_("You do not have permission to waive fines."))
        if not reason:
            frappe.throw(_("Please provide a reason for waiver."))

        self.status = "Waived"
        self.waiver_reason = reason
        self.outstanding = 0
        self.save(ignore_permissions=True)
        frappe.msgprint(_("Fine waived successfully."), alert=True)


    def create_sales_invoice(self):
        if self.sales_invoice:
            return
        if not frappe.db.exists("DocType", "Sales Invoice"):
            return
        if not self.customer:
            frappe.log_error("No customer linked to member", "Library Fine - Invoice Skipped")
            return

        try:
            income_account = frappe.db.get_single_value(
                "Library Settings", "library_income_account"
            )
            company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
                "Global Defaults", "default_company"
            )

            si = frappe.get_doc({
                "doctype": "Sales Invoice",
                "customer": self.customer,
                "company": company,
                "posting_date": today(),
                "due_date": today(),
                "items": [{
                    "item_name": "Library Fine",
                    "description": "Library overdue fine for Book Issue {0} — {1} day(s) overdue".format(
                        self.book_issue_reference, self.days_overdue
                    ),
                    "qty": 1,
                    "rate": self.fine_amount,
                    "income_account": income_account,
                }],
                "remarks": "Auto-generated from Library Fine {0}".format(self.name),
            })
            si.insert(ignore_permissions=True)
            si.submit()
            self.db_set("sales_invoice", si.name)
            frappe.msgprint(
                _("Sales Invoice {0} created.").format(si.name),
                alert=True
            )
        except Exception as e:
            frappe.log_error(str(e), "Library Fine - Sales Invoice Creation Failed")

    def cancel_sales_invoice(self):
        if not self.sales_invoice:
            return
        try:
            si = frappe.get_doc("Sales Invoice", self.sales_invoice)
            if si.docstatus == 1:
                si.cancel()
        except Exception as e:
            frappe.log_error(str(e), "Library Fine - Sales Invoice Cancel Failed")


    def update_member_summary(self):
        if not self.library_member:
            return
        member = frappe.get_doc("Library Member", self.library_member)
        member.update_summary()