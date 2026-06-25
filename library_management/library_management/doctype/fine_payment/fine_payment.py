# Copyright (c) 2026, Shivani Sahu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import today


class FinePayment(Document):

    def validate(self):
        self.validate_fine()
        self.validate_amount()
        self.set_defaults()

    def on_submit(self):
        self.update_fine_record()
        self.create_payment_entry()
        self.update_member_summary()

    def on_cancel(self):
        self.reverse_fine_record()
        self.cancel_payment_entry()
        self.update_member_summary()


    def validate_fine(self):
        if not self.library_fine:
            frappe.throw(_("Please select a Library Fine."))

        fine = frappe.get_doc("Library Fine", self.library_fine)

        if fine.status == "Paid":
            frappe.throw(_("This fine has already been fully paid."))

        if fine.status == "Waived":
            frappe.throw(_("This fine has been waived. No payment needed."))

        # Auto-fetch member
        if not self.library_member:
            self.library_member = fine.library_member

    def validate_amount(self):
        fine = frappe.get_doc("Library Fine", self.library_fine)
        outstanding = fine.fine_amount - (fine.amount_paid or 0)

        if not self.amount_paid or self.amount_paid <= 0:
            frappe.throw(_("Payment amount must be greater than zero."))

        if self.amount_paid > outstanding:
            frappe.throw(
                _("Payment amount ₹{0} exceeds outstanding amount ₹{1}.").format(
                    self.amount_paid, outstanding
                )
            )

    def set_defaults(self):
        if not self.payment_date:
            self.payment_date = today()
        if not self.recieved_by:
            self.recieved_by = frappe.session.user


    def update_fine_record(self):
        fine = frappe.get_doc("Library Fine", self.library_fine)
        new_paid = (fine.amount_paid or 0) + self.amount_paid
        new_outstanding = fine.fine_amount - new_paid

        if new_outstanding <= 0:
            new_status = "Paid"
            new_outstanding = 0
        else:
            new_status = "Partially Paid"

        frappe.db.set_value("Library Fine", self.library_fine, {
            "amount_paid": new_paid,
            "outstanding": new_outstanding,
            "status": new_status,
        })
        frappe.msgprint(
            _("Fine {0} updated. Status: {1}. Outstanding: ₹{2}").format(
                self.library_fine, new_status, new_outstanding
            ),
            alert=True
        )

    def create_payment_entry(self):
        if self.payment_entry:
            return
        if not frappe.db.exists("DocType", "Payment Entry"):
            return

        fine = frappe.get_doc("Library Fine", self.library_fine)
        customer = frappe.db.get_value("Library Member", self.library_member, "customer")
        if not customer:
            return

        try:
            company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
                "Global Defaults", "default_company"
            )
            receivable_account = frappe.db.get_value(
                "Company", company, "default_receivable_account"
            )
            cash_account = frappe.db.get_value(
                "Company", company, "default_cash_account"
            )

            pe = frappe.get_doc({
                "doctype": "Payment Entry",
                "payment_type": "Receive",
                "party_type": "Customer",
                "party": customer,
                "company": company,
                "posting_date": self.payment_date,
                "paid_amount": self.amount_paid,
                "received_amount": self.amount_paid,
                "paid_to": cash_account,
                "paid_from": receivable_account,
                "mode_of_payment": self.payment_mode,
                "reference_no": self.reference__transaction_no or self.name,
                "reference_date": self.payment_date,
                "remarks": "Library fine payment — {0}".format(self.library_fine),
            })
            pe.insert(ignore_permissions=True)
            pe.submit()
            self.db_set("payment_entry", pe.name)
            frappe.msgprint(
                _("Payment Entry {0} created.").format(pe.name),
                alert=True
            )
        except Exception as e:
            frappe.log_error(str(e), "Fine Payment - Payment Entry Creation Failed")


    def reverse_fine_record(self):
        fine = frappe.get_doc("Library Fine", self.library_fine)
        new_paid = max(0, (fine.amount_paid or 0) - self.amount_paid)
        new_outstanding = fine.fine_amount - new_paid

        if new_paid <= 0:
            new_status = "Unpaid"
        else:
            new_status = "Partially Paid"

        frappe.db.set_value("Library Fine", self.library_fine, {
            "amount_paid": new_paid,
            "outstanding": new_outstanding,
            "status": new_status,
        })

    def cancel_payment_entry(self):
        if not self.payment_entry:
            return
        try:
            pe = frappe.get_doc("Payment Entry", self.payment_entry)
            if pe.docstatus == 1:
                pe.cancel()
        except Exception as e:
            frappe.log_error(str(e), "Fine Payment - Payment Entry Cancel Failed")


    def update_member_summary(self):
        if not self.library_member:
            return
        member = frappe.get_doc("Library Member", self.library_member)
        member.update_summary()
