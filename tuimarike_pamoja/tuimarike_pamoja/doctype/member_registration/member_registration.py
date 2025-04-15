# Copyright (c) 2025, Kuria and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import random
from tuimarike_pamoja.services.rest import send_sms


class MemberRegistration(Document):
	def on_update(self):
		try:
			if self.workflow_state == "Approved":
				name_parts = self.full_name.split()
				first_name = name_parts[0] if len(name_parts) > 0 else ""
				middle_name = " ".join(name_parts[1:-1]) if len(name_parts) > 2 else ""
				last_name = name_parts[-1] if len(name_parts) > 1 else ""
				password = str(random.randint(1000, 9999))

				roles = [
					"Accounts Manager", "Accounts User", "Stock User", 
					"Sales Manager", "Sales Master Manager", "Sales User", 
					"Stock Manager", "Purchase Manager", "Purchase Master Manager", "Purchase User", "System Manager", "Item Manager"
				]
				
				system_modules = frappe.db.get_all("Module Def", fields=["name"])
				user_modules = ["Buying", "Accounts", "Stock", "Selling", "Core"]
				block_modules = [{"module": module["name"]} for module in system_modules if module["name"] not in user_modules]

				user_doc = frappe.get_doc({
					"doctype": "User",
					"email": self.email_address,
					"mobile_no": self.mobile_number,
					"first_name": first_name,
					"middle_name": middle_name,
					"last_name": last_name,
					"roles": [{"role": role} for role in roles],
					"block_modules":block_modules,
					"send_welcome_email": 0,
					"new_password": password
				})

				user_doc.insert(ignore_permissions=True) 
				frappe.db.commit()
				if user_doc.name:
					default_company = frappe.defaults.get_user_default("Company")
					message = (
							f"Welcome to {default_company}, {first_name}!\n\n"
							f"Your account has been successfully created. Below are your login credentials.\n\n"
							f"🔹 Username: {self.mobile_number}\n"
							f"🔹 Password: {password}\n\n"
							f"Best regards,\nThe {default_company} Team"
						)
					send_sms(self.mobile_number, message)
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"{e}")
			return {'error': str(e)}, 400
    
