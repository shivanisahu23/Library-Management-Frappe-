import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import getdate, today


class LibraryMember(Document):

    def before_insert(self):
        self.set_member_id()

    def validate(self):
        self.validate_dates()
        self.validate_email()
        self.set_membership_status()

    def after_insert(self):
        self.create_customer()

    def on_update(self):
        self.update_customer()


    def set_member_id(self):
        if not self.member_id:
            self.member_id = frappe.generate_hash(length=8).upper()


    def validate_dates(self):
        if self.membership_start_date and self.membership_expire_date:
            if getdate(self.membership_expire_date) <= getdate(self.membership_start_date):
                frappe.throw(_("Membership expiry date must be after start date."))

    def validate_email(self):
        if self.email:
            existing = frappe.db.get_value(
                "Library Member",
                {"email": self.email, "name": ("!=", self.name)},
                "name"
            )
            if existing:
                frappe.throw(_("A member with email {0} already exists: {1}").format(
                    self.email, existing
                ))

    def set_membership_status(self):
        if not self.membership_expire_date:
            return
        if self.membership_status == "Suspended":
            return  # don't auto-override suspended
        if getdate(self.membership_expire_date) < getdate(today()):
            self.membership_status = "Expired"
        else:
            self.membership_status = "Active"


    def create_customer(self):
        if self.customer:
            return
        if not frappe.db.exists("DocType", "Customer"):
            return  
        try:
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": self.full_name,
                "customer_type": "Individual",
                "customer_group": self._get_customer_group(),
                "territory": "All Territories",
            })
            customer.insert(ignore_permissions=True)
            self.db_set("customer", customer.name)
            frappe.msgprint(
                _("Customer {0} created automatically.").format(customer.name),
                alert=True
            )
        except Exception as e:
            frappe.log_error(str(e), "Library Member - Customer Creation Failed")

    def update_customer(self):
        if not self.customer:
            return
        try:
            frappe.db.set_value("Customer", self.customer, "customer_name", self.full_name)
        except Exception:
            pass

    def _get_customer_group(self):
        if frappe.db.exists("Customer Group", "Library Members"):
            return "Library Members"
        # fallback to default
        return frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups"


    def update_summary(self):
        issued_count = frappe.db.count("Book Issue", {
            "library_member": self.name,
            "status": ["in", ["Issues", "Overdue"]]
        })
        outstanding = frappe.db.sql("""
            SELECT IFNULL(SUM(outstanding), 0)
            FROM `tabLibrary Fine`
            WHERE library_member = %s
            AND status IN ('Unpaid', 'Partially Paid')
        """, self.name)[0][0]

        self.db_set("books_currently_issued", issued_count)
        self.db_set("outstanding_fine", outstanding)